"use strict";

const state = {
  screen: "overview",
  source: "default",
  file: null,
  preview: null,
  analysis: null,
  charts: {},
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const number = (value, digits = 2) =>
  value === null || value === undefined || Number.isNaN(Number(value))
    ? "—"
    : Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
const text = (value) => String(value ?? "—");
const escapeHtml = (value) =>
  text(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);

function showToast(message, kind = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${kind === "error" ? "error" : ""}`;
  toast.textContent = message;
  $("#alert-region").append(toast);
  window.setTimeout(() => toast.remove(), 4500);
}

function setButtonLoading(button, loading, label) {
  if (!button) return;
  if (loading) {
    button.dataset.label = button.textContent;
    button.textContent = label;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
  }
}

async function jsonRequest(url, options) {
  const response = await fetch(url, options);
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = { error: "The server returned an unreadable response." };
  }
  if (!response.ok) {
    throw new Error(payload.error || payload.message || `Request failed with status ${response.status}`);
  }
  return payload;
}

async function checkBackend() {
  const statusIndicator = $("#backend-status");
  const statusText = statusIndicator.querySelector(".status-text");
  try {
    const response = await fetch("/api/health", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Health check returned ${response.status}`);
    const data = await response.json();
    if (data.status !== "ok") throw new Error("Backend reported an unhealthy status");
    statusIndicator.className = "status status-online";
    statusText.textContent = "Backend connected";
    $("#system-backend").textContent = "Connected";
  } catch (error) {
    statusIndicator.className = "status status-offline";
    statusText.textContent = "Backend unavailable";
    $("#system-backend").textContent = "Unavailable";
    console.error("Backend health check failed:", error);
  }
}

function navigate(screen) {
  const target = $("[data-screen-panel=\"" + screen + "\"]");
  if (!target) return;
  state.screen = screen;
  $$(".screen").forEach((panel) => panel.classList.toggle("active", panel === target));
  $$(".sidebar nav .nav-item").forEach((item) => item.classList.toggle("active", item.dataset.screen === screen));
  $(".about").classList.remove("active");
  $("#sidebar").classList.remove("open");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (screen === "visualizations" && state.analysis) window.setTimeout(renderResultCharts, 0);
  if (screen === "findings" && state.analysis) window.setTimeout(renderMiniCharts, 0);
  if (screen === "overview" && state.analysis) window.setTimeout(renderQuickCharts, 0);
}

function currentFormData() {
  const form = new FormData();
  if (state.source === "upload") {
    if (!state.file) throw new Error("Choose a CSV file before continuing.");
    form.append("file", state.file);
  } else {
    form.append("source", "default");
  }
  return form;
}

async function loadPreview(source = state.source) {
  state.source = source;
  if (source === "upload" && !state.file) {
    throw new Error("Choose a CSV file before selecting the upload source.");
  }
  const payload = await jsonRequest("/api/preview", { method: "POST", body: currentFormData() });
  state.preview = payload.dataset;
  state.analysis = null;
  destroyCharts();
  syncSourceControls();
  renderPreview();
  resetAnalysisViews();
  return payload;
}

function syncSourceControls() {
  $("#default-source-option").checked = state.source === "default";
  $("#upload-source-option").checked = state.source === "upload";
  $("#selected-file-name").textContent = state.file ? state.file.name : "No custom file selected";
  $("#analysis-source-label").textContent = state.source === "default"
    ? "Default research dataset"
    : (state.file?.name || "Uploaded CSV");
}

function sumMissing(missing) {
  return Object.values(missing || {}).reduce((sum, value) => sum + Number(value || 0), 0);
}

function renderPreview() {
  const data = state.preview;
  if (!data) return;
  const missingTotal = sumMissing(data.missing_values);
  const cells = data.row_count * data.column_count;
  const missingSuffix = cells ? ` (${number((missingTotal / cells) * 100, 1)}%)` : "";
  $("#overview-records").textContent = number(data.row_count, 0);
  $("#overview-columns").textContent = number(data.column_count, 0);
  $("#overview-missing").textContent = number(missingTotal, 0);
  $("#overview-status").textContent = "Ready";
  $("#overview-status-detail").textContent = "Dataset loaded successfully";
  $("#dataset-records").textContent = number(data.row_count, 0);
  $("#dataset-columns").textContent = number(data.column_count, 0);
  $("#dataset-missing").textContent = number(missingTotal, 0) + missingSuffix;
  $("#dataset-snapshot").innerHTML = `
    <dl class="detail-list">
      <dt>Source</dt><dd>${escapeHtml(state.source === "default" ? data.source : state.file?.name || data.source)}</dd>
      <dt>Records</dt><dd>${number(data.row_count, 0)}</dd>
      <dt>Variables</dt><dd>${number(data.column_count, 0)}</dd>
      <dt>Missing</dt><dd>${number(missingTotal, 0)} values${missingSuffix}</dd>
      <dt>Duplicates</dt><dd>${number(data.duplicate_row_count, 0)}</dd>
      <dt>Format</dt><dd>CSV</dd>
    </dl>`;

  $("#column-count-badge").textContent = `${data.column_count} columns`;
  $("#columns-table").innerHTML = data.columns.map((column, index) => `
    <tr><td>${index + 1}</td><td title="${escapeHtml(column)}">${escapeHtml(column)}</td>
    <td><span class="badge">${escapeHtml(data.data_types[column])}</span></td>
    <td>${number(data.missing_values[column], 0)}</td></tr>`).join("");

  const shownColumns = data.columns.slice(0, 8);
  $("#preview-head").innerHTML = `<tr>${shownColumns.map((column) => `<th title="${escapeHtml(column)}">${escapeHtml(column)}</th>`).join("")}</tr>`;
  $("#preview-body").innerHTML = (data.preview || []).map((row) =>
    `<tr>${shownColumns.map((column) => `<td>${escapeHtml(row[column] === null ? "Missing" : row[column])}</td>`).join("")}</tr>`
  ).join("");
  $("#preview-count-badge").textContent = `Showing ${(data.preview || []).length} of ${number(data.row_count, 0)} rows`;

  const types = Object.values(data.data_types || {});
  const numeric = types.filter((type) => ["integer", "float"].includes(type)).length;
  $("#quality-missing").textContent = number(missingTotal, 0);
  $("#quality-duplicates").textContent = number(data.duplicate_row_count, 0);
  $("#quality-categorical").textContent = number(types.length - numeric, 0);
  $("#quality-numeric").textContent = number(numeric, 0);
  populateVariableSelectors();
}

function suggestedColumns(kind) {
  const suggestions = state.preview?.suggested_columns?.[kind] || [];
  return suggestions.filter((column) => state.preview.columns.includes(column));
}

function populateVariableSelectors() {
  if (!state.preview) return;
  const columns = state.preview.columns;
  const xSuggestions = suggestedColumns("connectivity");
  const ySuggestions = suggestedColumns("learning_outcomes");
  fillSelect($("#connectivity-select"), columns, xSuggestions[0] || columns[0]);
  const defaultY = ySuggestions.find((column) => column !== $("#connectivity-select").value)
    || columns.find((column) => column !== $("#connectivity-select").value) || columns[0];
  fillSelect($("#learning-select"), columns, defaultY);
  $("#connectivity-hints").textContent = xSuggestions.length
    ? `Suggested: ${xSuggestions.join(" · ")}`
    : "No connectivity-specific suggestion was detected; review the selected column.";
  $("#learning-hints").textContent = ySuggestions.length
    ? `Suggested: ${ySuggestions.join(" · ")}`
    : "No learning-specific suggestion was detected; review the selected column.";
  updateVariableDetails();
}

function fillSelect(select, columns, selected) {
  select.innerHTML = columns.map((column) =>
    `<option value="${escapeHtml(column)}" ${column === selected ? "selected" : ""}>${escapeHtml(column)}</option>`
  ).join("");
}

const descriptions = {
  "Internet facility in your locality": "Self-reported rating of internet facility in the student’s locality; it is not a measured Mbps value.",
  "Your interaction in online mode": "Self-reported interaction rating for online learning.",
  "Clearing doubts with faculties in online mode": "Self-reported rating of the online doubt-clearing experience.",
  "Performance in online": "Recorded online-learning performance measure.",
  "Your level of satisfaction in Online Education": "Ordered satisfaction response recorded by the survey.",
};

function variableCard(column, role) {
  if (!column || !state.preview) return "Select a variable.";
  const missing = state.preview.missing_values[column] || 0;
  const valid = state.preview.row_count - missing;
  return `<h4>${escapeHtml(column)} <span class="badge">${role}</span></h4>
    <dl><dt>Detected type</dt><dd>${escapeHtml(state.preview.data_types[column])}</dd>
    <dt>Valid values</dt><dd>${number(valid, 0)}</dd><dt>Missing values</dt><dd>${number(missing, 0)}</dd>
    <dt>Description</dt><dd>${escapeHtml(descriptions[column] || "No verified description is available; interpret using the CSV documentation.")}</dd></dl>`;
}

function updateVariableDetails() {
  $("#x-detail").classList.remove("empty");
  $("#y-detail").classList.remove("empty");
  $("#x-detail").innerHTML = variableCard($("#connectivity-select").value, "Independent variable");
  $("#y-detail").innerHTML = variableCard($("#learning-select").value, "Dependent variable");
}

async function acceptFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showToast("Only CSV files are accepted.", "error");
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast("The CSV exceeds the 5 MB upload limit.", "error");
    return;
  }
  const previousFile = state.file;
  const previousSource = state.source;
  state.file = file;
  state.source = "upload";
  syncSourceControls();
  try {
    await loadPreview("upload");
    showToast(`${file.name} loaded successfully.`);
    navigate("dataset");
  } catch (error) {
    state.file = previousFile;
    state.source = previousSource;
    syncSourceControls();
    showToast(error.message, "error");
  }
}

async function chooseDefault() {
  const previousSource = state.source;
  state.source = "default";
  syncSourceControls();
  try {
    await loadPreview("default");
    showToast("Default research dataset loaded.");
  } catch (error) {
    state.source = previousSource;
    syncSourceControls();
    showToast(error.message, "error");
  }
}

function resetAnalysisViews() {
  $("#results-empty").hidden = false;
  $("#results-content").hidden = true;
  $("#findings-empty").hidden = false;
  $("#findings-content").hidden = true;
  $("#report-empty").hidden = false;
  $("#report-content").hidden = true;
  $("#quick-visuals").className = "empty";
  $("#quick-visuals").textContent = "Run an analysis to populate verified charts.";
}

function invalidateAnalysis(message = "Variable selection changed; run a new analysis.") {
  if (!state.analysis) return;
  state.analysis = null;
  destroyCharts();
  resetAnalysisViews();
  $("#overview-status").textContent = "Ready";
  $("#overview-status-detail").textContent = message;
}

async function runAnalysis() {
  if (!state.preview) return showToast("Load a dataset first.", "error");
  const x = $("#connectivity-select").value;
  const y = $("#learning-select").value;
  if (!x || !y) return showToast("Select both variables.", "error");
  if (x === y) return showToast("Choose two different variables.", "error");
  const button = $("#run-analysis");
  setButtonLoading(button, true, "Running analysis…");
  try {
    const form = currentFormData();
    form.append("connectivity_column", x);
    form.append("learning_column", y);
    state.analysis = await jsonRequest("/api/analyze", { method: "POST", body: form });
    renderAnalysis();
    navigate("visualizations");
    showToast("Analysis completed successfully.");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setButtonLoading(button, false);
  }
}

function statForLearning() {
  return state.analysis?.descriptive_statistics?.learning_outcome || {};
}

function renderAnalysis() {
  const result = state.analysis;
  if (!result) return;
  const x = result.selected_variables.connectivity.column;
  const y = result.selected_variables.learning_outcome.column;
  const stats = statForLearning();
  $("#overview-status").textContent = "Complete";
  $("#overview-status-detail").textContent = `${number(result.sample_size, 0)} valid observations`;
  $("#results-empty").hidden = true;
  $("#results-content").hidden = false;
  $("#results-summary-line").textContent = `Verified analysis of ${x} and ${y} using the active dataset.`;
  $("#results-selected-pair").textContent = `${x} vs. ${y}`;
  $("#mean-label").textContent = `Mean (${y})`;
  $("#median-label").textContent = `Median (${y})`;
  $("#result-mean").textContent = number(stats.mean);
  $("#result-median").textContent = number(stats.median);
  $("#result-std").textContent = number(stats.sample_standard_deviation);
  $("#result-n").textContent = number(result.sample_size, 0);
  renderResultPanels();
  renderFindings();
  renderReport();
  $("#quick-visuals").className = "quick-chart-grid";
  $("#quick-visuals").innerHTML = `<div><b>${escapeHtml(x)}</b><div class="chart-box mini"><canvas id="quick-connectivity-chart"></canvas></div></div><div><b>${escapeHtml(y)}</b><div class="chart-box mini"><canvas id="quick-learning-chart"></canvas></div></div><button class="button secondary" data-screen="visualizations">Open full results</button>`;
  bindNavigation($("#quick-visuals"));
}

function renderResultPanels() {
  const result = state.analysis;
  const correlation = result.correlation;
  const regression = result.regression;
  const hypothesis = result.hypothesis_test;
  $("#correlation-result").innerHTML = `<h3>⌁ Spearman Correlation</h3><div class="result-table">
    <span>Coefficient (ρ)</span><b>${number(correlation.coefficient, 3)}</b><span>p-value</span><b>${formatP(correlation.p_value)}</b>
    <span>Direction</span><b>${escapeHtml(correlation.direction || "—")}</b><span>Valid pairs</span><b>${number(correlation.valid_pairs, 0)}</b></div>
    <p class="interpretation">${escapeHtml(correlation.interpretation || "No interpretation available.")}</p>`;
  if (regression.status === "available") {
    $("#regression-result").innerHTML = `<h3>⌁ Linear Regression</h3><div class="result-table">
      <span>Equation</span><b>${escapeHtml(regression.equation)}</b><span>Slope</span><b>${number(regression.slope, 3)}</b>
      <span>Intercept</span><b>${number(regression.intercept, 3)}</b><span>R-squared</span><b>${number(regression.r_squared, 3)}</b></div>
      <p class="interpretation">${escapeHtml(regression.interpretation || "")}</p>`;
  } else {
    $("#regression-result").innerHTML = `<h3>⌁ Linear Regression</h3><p class="interpretation unavailable"><b>Unavailable for this selection.</b><br>${escapeHtml(regression.reason || "The selected variables cannot be represented by this model.")}</p>`;
  }
  $("#hypothesis-result").innerHTML = `<h3>⚗ Hypothesis Test</h3><div class="result-table">
    <span>Method</span><b>${escapeHtml(hypothesis.method || "—")}</b><span>p-value</span><b>${formatP(hypothesis.p_value)}</b>
    <span>Alpha</span><b>${number(hypothesis.alpha, 3)}</b><span>Decision</span><b>${escapeHtml(hypothesis.decision || "—")}</b></div>
    <p class="interpretation">${escapeHtml(hypothesis.interpretation || "")}</p>`;
  const baseWarnings = [
    "This observational analysis identifies association, not causation.",
    "Self-reported survey values may contain response bias.",
  ];
  $("#results-warnings").innerHTML = [...baseWarnings, ...(result.warnings || [])]
    .map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
}

function formatP(value) {
  if (value === null || value === undefined) return "—";
  return Number(value) < 0.001 ? "< 0.001" : number(value, 4);
}

function destroyCharts() {
  Object.values(state.charts).forEach((chart) => chart?.destroy());
  state.charts = {};
}

function chartAvailable() {
  if (typeof window.Chart === "undefined") {
    showToast("Chart.js could not load. Check the network connection and reload.", "error");
    return false;
  }
  return true;
}

function replaceChart(key, canvas, config) {
  state.charts[key]?.destroy();
  state.charts[key] = new Chart(canvas, config);
}

function renderResultCharts() {
  if (!state.analysis || !chartAvailable()) return;
  const result = state.analysis;
  const visual = result.visualization_data;
  const x = result.selected_variables.connectivity.column;
  const y = result.selected_variables.learning_outcome.column;
  $("#scatter-title").textContent = `${x} vs. ${y}`;
  $("#learning-chart-title").textContent = `Distribution of ${y}`;
  $("#connectivity-chart-title").textContent = `Distribution of ${x}`;
  const points = (visual.scatter_points || []).map((point) => ({ x: Number(point.x), y: Number(point.y) }));
  const line = (visual.regression_line || []).map((point) => ({ x: Number(point.x), y: Number(point.y) }));
  replaceChart("scatter", $("#scatter-chart"), {
    type: "scatter",
    data: { datasets: [
      { label: "Observed values", data: points, backgroundColor: "rgba(8,124,240,.42)", pointRadius: 3 },
      ...(line.length ? [{ label: "Regression line", data: line, type: "line", borderColor: "#075fd0", borderDash: [6, 4], pointRadius: 0 }] : []),
    ] },
    options: chartOptions(x, y),
  });
  renderDistribution("learning", $("#learning-chart"), visual.distributions.learning_outcome || [], y, "#2587e9");
  renderDistribution("connectivity", $("#connectivity-chart"), visual.distributions.connectivity || [], x, "#18ae7a");
}

function chartOptions(x, y) {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { boxWidth: 12 } } },
    scales: { x: { title: { display: true, text: x } }, y: { title: { display: true, text: y } } },
  };
}

function renderDistribution(key, canvas, values, label, color) {
  replaceChart(key, canvas, {
    type: "bar",
    data: { labels: values.map((item) => text(item.value)), datasets: [{ label: "Count", data: values.map((item) => item.count), backgroundColor: color }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: label } }, y: { beginAtZero: true, title: { display: true, text: "Observations" } } } },
  });
}

function significanceSentence() {
  const hypothesis = state.analysis.hypothesis_test;
  const significant = hypothesis.p_value !== null && Number(hypothesis.p_value) < Number(hypothesis.alpha);
  return significant
    ? `The association is statistically significant at α = ${number(hypothesis.alpha, 3)} (p ${formatP(hypothesis.p_value).startsWith("<") ? formatP(hypothesis.p_value) : "= " + formatP(hypothesis.p_value)}).`
    : `The analysis does not find a statistically significant association at α = ${number(hypothesis.alpha, 3)}.`;
}

function renderFindings() {
  const result = state.analysis;
  const x = result.selected_variables.connectivity.column;
  const y = result.selected_variables.learning_outcome.column;
  const correlation = result.correlation;
  const direction = (correlation.direction || "undetermined").toLowerCase();
  const association = correlation.coefficient === null
    ? `The association between ${x} and ${y} could not be estimated.`
    : `A ${direction} association was observed between ${x} and ${y} (Spearman ρ = ${number(correlation.coefficient, 3)}).`;
  $("#findings-empty").hidden = true;
  $("#findings-content").hidden = false;
  $("#findings-banner-text").textContent = `${association} The result describes association and must not be interpreted as proof of causation.`;
  const findings = [
    ["Association", association],
    ["Valid observations", `${number(result.sample_size, 0)} complete paired observations were used after missing-value handling.`],
    ["Statistical evidence", significanceSentence()],
  ];
  $("#main-findings").innerHTML = findings.map((item, index) => `<div class="finding"><b>${index + 1}</b><div><h4>${escapeHtml(item[0])}</h4><p>${escapeHtml(item[1])}</p></div></div>`).join("");
  $("#plain-interpretation").textContent = correlation.interpretation || association;
  const limitations = [
    "The source is observational and self-reported, so causal conclusions are not supported.",
    "Survey scales and encoded categories require context-aware interpretation.",
    `Missing values reduced the usable paired sample to ${number(result.sample_size, 0)} observations.`,
    ...(result.warnings || []),
  ];
  $("#findings-limitations").innerHTML = limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#report-ready-summary").innerHTML = `
    <div class="summary-block"><b>Objective</b><div>Assess the association between ${escapeHtml(x)} and ${escapeHtml(y)}.</div></div>
    <div class="summary-block"><b>Dataset</b><div>${number(result.dataset.row_count, 0)} rows; ${number(result.dataset.column_count, 0)} variables.</div></div>
    <div class="summary-block"><b>Methods</b><div>Descriptive statistics, Spearman correlation, linear regression when applicable, and hypothesis testing.</div></div>
    <div class="summary-block"><b>Result</b><div>${escapeHtml(association)} ${escapeHtml(significanceSentence())}</div></div>`;
}

function renderMiniCharts() {
  if (!state.analysis || !chartAvailable()) return;
  const visual = state.analysis.visualization_data;
  renderDistribution("miniConnectivity", $("#mini-connectivity-chart"), visual.distributions.connectivity || [], state.analysis.selected_variables.connectivity.column, "#18ae7a");
  renderDistribution("miniLearning", $("#mini-learning-chart"), visual.distributions.learning_outcome || [], state.analysis.selected_variables.learning_outcome.column, "#2587e9");
}

function renderQuickCharts() {
  if (!state.analysis || !chartAvailable()) return;
  const visual = state.analysis.visualization_data;
  renderDistribution("quickConnectivity", $("#quick-connectivity-chart"), visual.distributions.connectivity || [], state.analysis.selected_variables.connectivity.column, "#18ae7a");
  renderDistribution("quickLearning", $("#quick-learning-chart"), visual.distributions.learning_outcome || [], state.analysis.selected_variables.learning_outcome.column, "#2587e9");
}

function renderReport() {
  const result = state.analysis;
  const x = result.selected_variables.connectivity.column;
  const y = result.selected_variables.learning_outcome.column;
  $("#report-empty").hidden = true;
  $("#report-content").hidden = false;
  $("#report-overview").innerHTML = `<h2>Connectivity and Online Learning Analysis</h2><p><b>Variables:</b> ${escapeHtml(x)} and ${escapeHtml(y)}</p><p><b>Source:</b> ${escapeHtml(result.dataset.source)}</p>`;
  $("#report-statistics").innerHTML = `<h3>Statistical summary</h3><p>Valid observations: ${number(result.sample_size, 0)}. Spearman coefficient: ${number(result.correlation.coefficient, 3)}. p-value: ${formatP(result.correlation.p_value)}.</p>`;
  $("#report-finding").innerHTML = `<h3>Finding</h3><p>${escapeHtml(result.correlation.interpretation || "No interpretation available.")} ${escapeHtml(significanceSentence())}</p>`;
  $("#report-limitations").innerHTML = "<h3>Limitations</h3><p>This analysis is observational and based on survey responses. Association does not establish causation.</p>";
}

function reportText() {
  if (!state.analysis) return "";
  const result = state.analysis;
  return [
    "Internet Speed and Online Learning Experience",
    `Variables: ${result.selected_variables.connectivity.column} vs. ${result.selected_variables.learning_outcome.column}`,
    `Valid observations: ${result.sample_size}`,
    `Spearman coefficient: ${number(result.correlation.coefficient, 3)}`,
    `p-value: ${formatP(result.correlation.p_value)}`,
    `Interpretation: ${result.correlation.interpretation || "Unavailable"}`,
    significanceSentence(),
    "Limitation: This observational analysis does not establish causation.",
  ].join("\n");
}

async function copyResults() {
  try {
    await navigator.clipboard.writeText(reportText());
    showToast("Results copied to the clipboard.");
  } catch {
    showToast("Clipboard access was unavailable. Use the Report screen to copy manually.", "error");
  }
}

async function downloadPdf(button) {
  if (!state.analysis) {
    showToast("Run an analysis before downloading a report.", "error");
    return;
  }
  setButtonLoading(button, true, "Generating PDF…");
  try {
    const form = currentFormData();
    form.append("connectivity_column", state.analysis.selected_variables.connectivity.column);
    form.append("learning_column", state.analysis.selected_variables.learning_outcome.column);
    const response = await fetch("/api/report/pdf", { method: "POST", body: form });
    if (!response.ok) {
      let message = "PDF generation failed.";
      try {
        const payload = await response.json();
        message = payload.message || message;
      } catch {
        // Keep the generic message when the failure is not JSON.
      }
      throw new Error(message);
    }
    const contentType = response.headers.get("Content-Type") || "";
    if (!contentType.includes("application/pdf")) {
      throw new Error("The server did not return a valid PDF response.");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "NetLearn_Analysis_Report.pdf";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast("PDF report downloaded successfully.");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    setButtonLoading(button, false);
  }
}

function bindNavigation(root = document) {
  root.querySelectorAll("[data-screen]").forEach((element) => {
    if (element.dataset.bound) return;
    element.dataset.bound = "true";
    element.addEventListener("click", (event) => {
      event.preventDefault();
      navigate(element.dataset.screen);
    });
  });
}

function bindEvents() {
  bindNavigation();
  const openFilePicker = () => {
    $("#csv-input").value = "";
    $("#csv-input").click();
  };
  $("#menu-toggle").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
  $("#load-default-top").addEventListener("click", async () => { await chooseDefault(); navigate("dataset"); });
  $("#upload-top").addEventListener("click", openFilePicker);
  $("#csv-input").addEventListener("change", (event) => acceptFile(event.target.files[0]));
  $("#drop-zone").addEventListener("click", openFilePicker);
  $("#drop-zone").addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") openFilePicker();
  });
  ["dragenter", "dragover"].forEach((name) => $("#drop-zone").addEventListener(name, (event) => {
    event.preventDefault(); $("#drop-zone").classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach((name) => $("#drop-zone").addEventListener(name, (event) => {
    event.preventDefault(); $("#drop-zone").classList.remove("dragover");
  }));
  $("#drop-zone").addEventListener("drop", (event) => acceptFile(event.dataTransfer.files[0]));
  $$("input[name=dataset-source]").forEach((radio) => radio.addEventListener("change", async (event) => {
    const next = event.target.value;
    if (next === "upload" && !state.file) {
      openFilePicker();
      syncSourceControls();
      return;
    }
    try { await loadPreview(next); } catch (error) { showToast(error.message, "error"); syncSourceControls(); }
  }));
  $("#proceed-analysis").addEventListener("click", () => state.preview ? navigate("analysis") : showToast("Load a dataset first.", "error"));
  $("#connectivity-select").addEventListener("change", () => {
    updateVariableDetails();
    invalidateAnalysis();
  });
  $("#learning-select").addEventListener("change", () => {
    updateVariableDetails();
    invalidateAnalysis();
  });
  $("#run-analysis").addEventListener("click", runAnalysis);
  $("#copy-results").addEventListener("click", copyResults);
  $("#start-new-analysis").addEventListener("click", () => navigate("analysis"));
  $("#download-findings-pdf").addEventListener("click", (event) => downloadPdf(event.currentTarget));
  $("#download-report-pdf").addEventListener("click", (event) => downloadPdf(event.currentTarget));
}

async function initialize() {
  bindEvents();
  checkBackend();
  window.setInterval(checkBackend, 30_000);
  try {
    await loadPreview("default");
  } catch (error) {
    $("#dataset-snapshot").textContent = "The default dataset could not be loaded.";
    showToast(error.message, "error");
  }
}

initialize();
