#include <lv2/core/lv2.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace {

static constexpr const char* PLUGIN_URI = "https://example.org/lv2/vocal2midi";

enum PortIndex : uint32_t {
  AUDIO_IN = 0,
  AUDIO_OUT,
  ANALYZE_TRIGGER,
  QUANTIZE_GRID,
  QUANTIZE_STRENGTH,
  MIN_NOTE_MS,
  GAP_MERGE_MS,
  VIBRATO_SMOOTHING,
  MIN_CONFIDENCE,
  OCTAVE_SHIFT,
  START_OFFSET_MS,
  EXPORT_TRIGGER
};

struct Params {
  float quantizeGrid{0.0F};
  float quantizeStrength{1.0F};
  float minNoteMs{80.0F};
  float gapMergeMs{40.0F};
  float vibratoSmoothing{0.5F};
  float minConfidence{0.4F};
  float octaveShift{0.0F};
  float startOffsetMs{0.0F};
};

struct Vocal2MidiPlugin {
  const float* audioIn{nullptr};
  float* audioOut{nullptr};

  const float* analyzeTrigger{nullptr};
  const float* quantizeGrid{nullptr};
  const float* quantizeStrength{nullptr};
  const float* minNoteMs{nullptr};
  const float* gapMergeMs{nullptr};
  const float* vibratoSmoothing{nullptr};
  const float* minConfidence{nullptr};
  const float* octaveShift{nullptr};
  const float* startOffsetMs{nullptr};
  const float* exportTrigger{nullptr};

  double sampleRate{48000.0};
  float lastAnalyzeGate{0.0F};
  float lastExportGate{0.0F};

  std::vector<float> captureBuffer;
  size_t maxCaptureSamples{0};

  std::mutex workerMutex;
  std::atomic<bool> workerBusy{false};

  std::filesystem::path workDir{"/tmp/vocal2midi"};
  std::filesystem::path lastMidiFile;

  Vocal2MidiPlugin(double sr) : sampleRate(sr) {
    constexpr double maxCaptureSeconds = 120.0;
    maxCaptureSamples = static_cast<size_t>(sampleRate * maxCaptureSeconds);
    captureBuffer.reserve(maxCaptureSamples);
    std::error_code ec;
    std::filesystem::create_directories(workDir, ec);
  }
};

static std::string nowStamp() {
  const auto now = std::chrono::system_clock::now();
  const auto t = std::chrono::system_clock::to_time_t(now);
  return std::to_string(static_cast<long long>(t));
}

static bool writeMonoWav(const std::filesystem::path& filePath, const std::vector<float>& samples, uint32_t sampleRate) {
  std::ofstream out(filePath, std::ios::binary);
  if (!out) {
    return false;
  }

  const uint16_t channels = 1;
  const uint16_t bitsPerSample = 16;
  const uint16_t blockAlign = channels * (bitsPerSample / 8);
  const uint32_t byteRate = sampleRate * blockAlign;
  const uint32_t dataSize = static_cast<uint32_t>(samples.size() * blockAlign);
  const uint32_t riffSize = 36 + dataSize;

  out.write("RIFF", 4);
  out.write(reinterpret_cast<const char*>(&riffSize), 4);
  out.write("WAVE", 4);
  out.write("fmt ", 4);

  const uint32_t fmtSize = 16;
  const uint16_t formatTag = 1;
  out.write(reinterpret_cast<const char*>(&fmtSize), 4);
  out.write(reinterpret_cast<const char*>(&formatTag), 2);
  out.write(reinterpret_cast<const char*>(&channels), 2);
  out.write(reinterpret_cast<const char*>(&sampleRate), 4);
  out.write(reinterpret_cast<const char*>(&byteRate), 4);
  out.write(reinterpret_cast<const char*>(&blockAlign), 2);
  out.write(reinterpret_cast<const char*>(&bitsPerSample), 2);

  out.write("data", 4);
  out.write(reinterpret_cast<const char*>(&dataSize), 4);

  for (const float sample : samples) {
    const float clamped = std::fmax(-1.0F, std::fmin(1.0F, sample));
    const int16_t pcm = static_cast<int16_t>(clamped * 32767.0F);
    out.write(reinterpret_cast<const char*>(&pcm), sizeof(pcm));
  }

  return true;
}

static Params readParams(const Vocal2MidiPlugin* self) {
  Params p;
  p.quantizeGrid = self->quantizeGrid ? *self->quantizeGrid : p.quantizeGrid;
  p.quantizeStrength = self->quantizeStrength ? *self->quantizeStrength : p.quantizeStrength;
  p.minNoteMs = self->minNoteMs ? *self->minNoteMs : p.minNoteMs;
  p.gapMergeMs = self->gapMergeMs ? *self->gapMergeMs : p.gapMergeMs;
  p.vibratoSmoothing = self->vibratoSmoothing ? *self->vibratoSmoothing : p.vibratoSmoothing;
  p.minConfidence = self->minConfidence ? *self->minConfidence : p.minConfidence;
  p.octaveShift = self->octaveShift ? *self->octaveShift : p.octaveShift;
  p.startOffsetMs = self->startOffsetMs ? *self->startOffsetMs : p.startOffsetMs;
  return p;
}

static void runBridge(Vocal2MidiPlugin* self, const std::vector<float>& snapshot, const Params& params, bool exportOnly) {
  if (self->workerBusy.exchange(true)) {
    return;
  }

  std::thread worker([self, snapshot, params, exportOnly]() {
    std::lock_guard<std::mutex> lock(self->workerMutex);

    const std::string stamp = nowStamp();
    const auto wavPath = self->workDir / ("capture_" + stamp + ".wav");
    const auto midiPath = self->workDir / ("capture_" + stamp + ".mid");

    if (!exportOnly && !writeMonoWav(wavPath, snapshot, static_cast<uint32_t>(self->sampleRate))) {
      self->workerBusy = false;
      return;
    }

    std::ostringstream cmd;
    cmd << "python3 scripts/vocal2midi_bridge.py"
        << " --input \"" << wavPath.string() << "\""
        << " --output \"" << midiPath.string() << "\"";

    if (exportOnly) {
      cmd << " --copy-from \"" << self->lastMidiFile.string() << "\"";
    }

    cmd
        << " --quantize-grid " << static_cast<int>(params.quantizeGrid)
        << " --quantize-strength " << params.quantizeStrength
        << " --min-note-ms " << params.minNoteMs
        << " --gap-merge-ms " << params.gapMergeMs
        << " --vibrato-smoothing " << params.vibratoSmoothing
        << " --min-confidence " << params.minConfidence
        << " --octave-shift " << static_cast<int>(params.octaveShift)
        << " --start-offset-ms " << params.startOffsetMs;

    const int rc = std::system(cmd.str().c_str());
    if (rc == 0) {
      self->lastMidiFile = midiPath;
    }

    self->workerBusy = false;
  });

  worker.detach();
}

static LV2_Handle instantiate(const LV2_Descriptor*, double rate, const char*, const LV2_Feature* const*) {
  return new Vocal2MidiPlugin(rate);
}

static void connect_port(LV2_Handle instance, uint32_t port, void* data) {
  auto* self = static_cast<Vocal2MidiPlugin*>(instance);
  switch (port) {
    case AUDIO_IN: self->audioIn = static_cast<const float*>(data); break;
    case AUDIO_OUT: self->audioOut = static_cast<float*>(data); break;
    case ANALYZE_TRIGGER: self->analyzeTrigger = static_cast<const float*>(data); break;
    case QUANTIZE_GRID: self->quantizeGrid = static_cast<const float*>(data); break;
    case QUANTIZE_STRENGTH: self->quantizeStrength = static_cast<const float*>(data); break;
    case MIN_NOTE_MS: self->minNoteMs = static_cast<const float*>(data); break;
    case GAP_MERGE_MS: self->gapMergeMs = static_cast<const float*>(data); break;
    case VIBRATO_SMOOTHING: self->vibratoSmoothing = static_cast<const float*>(data); break;
    case MIN_CONFIDENCE: self->minConfidence = static_cast<const float*>(data); break;
    case OCTAVE_SHIFT: self->octaveShift = static_cast<const float*>(data); break;
    case START_OFFSET_MS: self->startOffsetMs = static_cast<const float*>(data); break;
    case EXPORT_TRIGGER: self->exportTrigger = static_cast<const float*>(data); break;
    default: break;
  }
}

static void activate(LV2_Handle instance) {
  auto* self = static_cast<Vocal2MidiPlugin*>(instance);
  self->captureBuffer.clear();
  self->lastAnalyzeGate = 0.0F;
  self->lastExportGate = 0.0F;
}

static void run(LV2_Handle instance, uint32_t sampleCount) {
  auto* self = static_cast<Vocal2MidiPlugin*>(instance);
  if (!self->audioIn || !self->audioOut) {
    return;
  }

  for (uint32_t i = 0; i < sampleCount; ++i) {
    const float s = self->audioIn[i];
    self->audioOut[i] = s;
    if (self->captureBuffer.size() < self->maxCaptureSamples) {
      self->captureBuffer.push_back(s);
    } else {
      self->captureBuffer.erase(self->captureBuffer.begin());
      self->captureBuffer.push_back(s);
    }
  }

  const float analyzeGate = self->analyzeTrigger ? *self->analyzeTrigger : 0.0F;
  const float exportGate = self->exportTrigger ? *self->exportTrigger : 0.0F;

  const bool analyzeRising = (analyzeGate > 0.5F) && (self->lastAnalyzeGate <= 0.5F);
  const bool exportRising = (exportGate > 0.5F) && (self->lastExportGate <= 0.5F);
  self->lastAnalyzeGate = analyzeGate;
  self->lastExportGate = exportGate;

  if (analyzeRising) {
    runBridge(self, self->captureBuffer, readParams(self), false);
  }
  if (exportRising && !self->lastMidiFile.empty()) {
    runBridge(self, {}, readParams(self), true);
  }
}

static void deactivate(LV2_Handle) {}

static void cleanup(LV2_Handle instance) {
  delete static_cast<Vocal2MidiPlugin*>(instance);
}

static const void* extension_data(const char*) { return nullptr; }

static const LV2_Descriptor descriptor{
  PLUGIN_URI,
  instantiate,
  connect_port,
  activate,
  run,
  deactivate,
  cleanup,
  extension_data
};

}  // namespace

extern "C" const LV2_Descriptor* lv2_descriptor(uint32_t index) {
  return index == 0 ? &descriptor : nullptr;
}
