/* ChemLab Analytics — shared frontend helpers */

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  return data;
}

async function postForm(url, formData) {
  const res = await fetch(url, { method: "POST", body: formData });
  return res.json();
}

function renderKV(pairs) {
  return pairs.map(
    ([k, v]) => `<div class="kv"><span class="k">${k}</span><span class="v">${v}</span></div>`
  ).join("");
}

function showResult(boxEl, html, isError = false) {
  boxEl.classList.toggle("error", isError);
  boxEl.style.display = "block";
  boxEl.innerHTML = html;
}

function showError(boxEl, message) {
  showResult(boxEl, `⚠ ${message}`, true);
}

function parseValueList(text) {
  return text
    .split(/[,\s]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map(Number);
}

function fieldOrNull(id) {
  const v = document.getElementById(id).value;
  return v === "" ? null : v;
}
