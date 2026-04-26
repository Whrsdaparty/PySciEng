const form = document.getElementById("allocation-form");
const profileSelect = document.getElementById("active-profile");
const tradeForm = document.getElementById("trade-form");
const equityForm = document.getElementById("equity-form");

const fields = {
  startingCash: document.getElementById("starting_cash"),
  low: document.getElementById("low"),
  medium: document.getElementById("medium"),
  high: document.getElementById("high"),
  fine: document.getElementById("fine_adjustment"),
  target: document.getElementById("target_daily_return_percent"),
  loss: document.getElementById("max_daily_loss_percent"),
};

const outputs = {
  lowNormalized: document.getElementById("low-normalized"),
  mediumNormalized: document.getElementById("medium-normalized"),
  highNormalized: document.getElementById("high-normalized"),
  lowCardPercent: document.getElementById("low-card-percent"),
  mediumCardPercent: document.getElementById("medium-card-percent"),
  highCardPercent: document.getElementById("high-card-percent"),
  lowDollars: document.getElementById("low-dollars"),
  mediumDollars: document.getElementById("medium-dollars"),
  highDollars: document.getElementById("high-dollars"),
  fine: document.getElementById("fine-output"),
  target: document.getElementById("target-output"),
  loss: document.getElementById("loss-output"),
  apiResult: document.getElementById("api-result"),
  jargonNotes: document.getElementById("jargon-notes"),
  tradeStatus: document.getElementById("trade-status"),
  equityStatus: document.getElementById("equity-status"),
  tradeHistoryBody: document.getElementById("trade-history-body"),
  equityHistoryBody: document.getElementById("equity-history-body"),
  summaryAccountValue: document.getElementById("summary-account-value"),
  summaryRealized: document.getElementById("summary-realized"),
  summaryUnrealized: document.getElementById("summary-unrealized"),
};

function activeProfile() {
  return profileSelect?.value || "simulation";
}

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value || 0));
}

function dateTime(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function getPayload() {
  return {
    starting_cash: Number(fields.startingCash.value),
    low: Number(fields.low.value),
    medium: Number(fields.medium.value),
    high: Number(fields.high.value),
    fine_adjustment: Number(fields.fine.value),
    target_daily_return_percent: Number(fields.target.value),
    max_daily_loss_percent: Number(fields.loss.value),
  };
}

function normalizeLocal() {
  const payload = getPayload();
  const highAdjusted = Math.min(100, Math.max(0, payload.high + payload.fine_adjustment));
  const total = payload.low + payload.medium + highAdjusted || 1;

  const lowPct = (payload.low / total) * 100;
  const mediumPct = (payload.medium / total) * 100;
  const highPct = (highAdjusted / total) * 100;
  const cash = payload.starting_cash || 0;

  outputs.lowNormalized.textContent = lowPct.toFixed(2);
  outputs.mediumNormalized.textContent = mediumPct.toFixed(2);
  outputs.highNormalized.textContent = highPct.toFixed(2);
  outputs.lowCardPercent.textContent = lowPct.toFixed(2);
  outputs.mediumCardPercent.textContent = mediumPct.toFixed(2);
  outputs.highCardPercent.textContent = highPct.toFixed(2);
  outputs.lowDollars.textContent = currency(cash * lowPct / 100);
  outputs.mediumDollars.textContent = currency(cash * mediumPct / 100);
  outputs.highDollars.textContent = currency(cash * highPct / 100);
  outputs.fine.textContent = payload.fine_adjustment.toFixed(2);
  outputs.target.textContent = payload.target_daily_return_percent.toFixed(2);
  outputs.loss.textContent = payload.max_daily_loss_percent.toFixed(2);
}

function renderJargonNotes(notes) {
  outputs.jargonNotes.innerHTML = notes
    .map((note) => `
      <article class="jargon-card">
        <div class="d-flex justify-content-between align-items-start gap-3">
          <h3 class="h5 mb-2">${note.term}</h3>
          <a href="${note.source_url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-secondary">Source</a>
        </div>
        <p class="mb-2"><strong>Plain English:</strong> ${note.plain_english}</p>
        <p class="mb-2"><strong>Why it matters here:</strong> ${note.why_it_matters_here}</p>
        <p class="small text-secondary mb-0">Source: ${note.source_name}</p>
      </article>
    `)
    .join("");
}

async function loadJargonNotes() {
  if (!outputs.jargonNotes) return;

  try {
    const response = await fetch("/static/data/jargon_notes.json");
    if (!response.ok) throw new Error("Unable to load jargon notes.");
    const notes = await response.json();
    renderJargonNotes(notes);
  } catch (error) {
    outputs.jargonNotes.textContent = error.message;
  }
}

async function submitAllocation(event) {
  event.preventDefault();
  normalizeLocal();

  const response = await fetch("/api/allocate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(getPayload()),
  });

  if (!response.ok) {
    outputs.apiResult.textContent = await response.text();
    return;
  }

  const result = await response.json();
  outputs.apiResult.textContent = JSON.stringify(result, null, 2);
}

function tradePayload() {
  return {
    profile: activeProfile(),
    symbol: document.getElementById("trade-symbol").value.trim().toUpperCase(),
    side: document.getElementById("trade-side").value,
    shares: Number(document.getElementById("trade-shares").value),
    price: Number(document.getElementById("trade-price").value),
    fees: Number(document.getElementById("trade-fees").value || 0),
    risk_bucket: document.getElementById("trade-risk-bucket").value,
    strategy_name: document.getElementById("trade-strategy").value.trim(),
    notes: document.getElementById("trade-notes").value.trim(),
  };
}

async function saveTrade(event) {
  event.preventDefault();
  outputs.tradeStatus.textContent = "Saving trade...";

  const response = await fetch("/api/trades", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tradePayload()),
  });

  if (!response.ok) {
    outputs.tradeStatus.textContent = await response.text();
    return;
  }

  outputs.tradeStatus.textContent = `Trade saved to ${activeProfile()} database.`;
  tradeForm.reset();
  document.getElementById("trade-fees").value = "0.00";
  await loadTrades();
}

async function loadTrades() {
  const response = await fetch(`/api/trades/${activeProfile()}`);
  if (!response.ok) {
    outputs.tradeHistoryBody.innerHTML = `<tr><td colspan="8">${await response.text()}</td></tr>`;
    return;
  }

  const result = await response.json();
  if (!result.trades.length) {
    outputs.tradeHistoryBody.innerHTML = `<tr><td colspan="8" class="text-secondary">No trades recorded for ${activeProfile()}.</td></tr>`;
    return;
  }

  outputs.tradeHistoryBody.innerHTML = result.trades
    .map((trade) => `
      <tr>
        <td>${dateTime(trade.trade_time)}</td>
        <td><strong>${trade.symbol}</strong></td>
        <td><span class="badge ${trade.side === "buy" ? "text-bg-success" : "text-bg-danger"}">${trade.side}</span></td>
        <td>${trade.shares}</td>
        <td>${currency(trade.price)}</td>
        <td>${currency(trade.fees)}</td>
        <td>${trade.risk_bucket}</td>
        <td>${trade.strategy_name || "-"}</td>
      </tr>
    `)
    .join("");
}

function equityPayload() {
  return {
    profile: activeProfile(),
    cash: Number(document.getElementById("snapshot-cash").value),
    open_position_value: Number(document.getElementById("snapshot-open-value").value),
    realized_gain_total: Number(document.getElementById("snapshot-realized").value),
    unrealized_gain_total: Number(document.getElementById("snapshot-unrealized").value),
    notes: document.getElementById("snapshot-notes").value.trim(),
  };
}

async function saveEquitySnapshot(event) {
  event.preventDefault();
  outputs.equityStatus.textContent = "Saving equity snapshot...";

  const response = await fetch("/api/equity-snapshots", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(equityPayload()),
  });

  if (!response.ok) {
    outputs.equityStatus.textContent = await response.text();
    return;
  }

  outputs.equityStatus.textContent = `Snapshot saved to ${activeProfile()} database.`;
  document.getElementById("snapshot-notes").value = "";
  await loadEquitySnapshots();
}

async function loadEquitySnapshots() {
  const response = await fetch(`/api/equity-snapshots/${activeProfile()}`);
  if (!response.ok) {
    outputs.equityHistoryBody.innerHTML = `<tr><td colspan="7">${await response.text()}</td></tr>`;
    return;
  }

  const result = await response.json();
  if (!result.snapshots.length) {
    outputs.equityHistoryBody.innerHTML = `<tr><td colspan="7" class="text-secondary">No equity snapshots recorded for ${activeProfile()}.</td></tr>`;
    outputs.summaryAccountValue.textContent = currency(0);
    outputs.summaryRealized.textContent = currency(0);
    outputs.summaryUnrealized.textContent = currency(0);
    return;
  }

  const latest = result.snapshots[0];
  outputs.summaryAccountValue.textContent = currency(latest.account_value);
  outputs.summaryRealized.textContent = currency(latest.realized_gain_total);
  outputs.summaryUnrealized.textContent = currency(latest.unrealized_gain_total);

  outputs.equityHistoryBody.innerHTML = result.snapshots
    .map((snapshot) => `
      <tr>
        <td>${dateTime(snapshot.created_at)}</td>
        <td>${currency(snapshot.cash)}</td>
        <td>${currency(snapshot.open_position_value)}</td>
        <td>${currency(snapshot.realized_gain_total)}</td>
        <td>${currency(snapshot.unrealized_gain_total)}</td>
        <td><strong>${currency(snapshot.account_value)}</strong></td>
        <td>${snapshot.notes || "-"}</td>
      </tr>
    `)
    .join("");
}

async function refreshHistory() {
  await Promise.all([loadTrades(), loadEquitySnapshots()]);
}

Object.values(fields).forEach((field) => {
  field.addEventListener("input", normalizeLocal);
});

form.addEventListener("submit", submitAllocation);
tradeForm.addEventListener("submit", saveTrade);
equityForm.addEventListener("submit", saveEquitySnapshot);
profileSelect.addEventListener("change", refreshHistory);
document.getElementById("refresh-trades").addEventListener("click", loadTrades);
document.getElementById("refresh-equity").addEventListener("click", loadEquitySnapshots);

normalizeLocal();
loadJargonNotes();
refreshHistory();
