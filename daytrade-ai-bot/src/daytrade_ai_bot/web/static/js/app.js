const form = document.getElementById("allocation-form");

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
};

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
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

async function submitAllocation(event) {
  event.preventDefault();
  normalizeLocal();

  const response = await fetch("/api/allocate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(getPayload()),
  });

  if (!response.ok) {
    const errorText = await response.text();
    outputs.apiResult.textContent = errorText;
    return;
  }

  const result = await response.json();
  outputs.apiResult.textContent = JSON.stringify(result, null, 2);
}

Object.values(fields).forEach((field) => {
  field.addEventListener("input", normalizeLocal);
});

form.addEventListener("submit", submitAllocation);
normalizeLocal();
