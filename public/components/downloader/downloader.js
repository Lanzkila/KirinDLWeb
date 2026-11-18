/* Live downloader API client. Progress is read from the backend, never simulated. */
const mediaInput = document.querySelector("#media-url");
const feedback = document.querySelector("#form-feedback");
const engineSelect = document.querySelector("#engine-select");
const form = document.querySelector("#download-form");
const submitButton = document.querySelector("#analyse-button");
const taskFlow = document.querySelector("#task-flow");
const progressPanel = document.querySelector("#progress-panel");
const downloadsPanel = document.querySelector("#downloads-panel");
const taskUrl = document.querySelector("#task-url");
const taskStatus = document.querySelector("#task-status");
const taskState = document.querySelector("#task-state");
const videoBar = document.querySelector("#video-bar");
const audioBar = document.querySelector("#audio-bar");
const videoPercent = document.querySelector("#video-percent");
const audioPercent = document.querySelector("#audio-percent");
const streamProgressList = document.querySelector("#stream-progress-list");
const galleryProgress = document.querySelector("#gallery-progress");
const galleryCount = document.querySelector("#gallery-count");
const processingStep = document.querySelector("#processing-step");
const mergingStep = document.querySelector("#merging-step");
const processingStatus = document.querySelector("#processing-status");
const mergingStatus = document.querySelector("#merging-status");
const readyIcon = document.querySelector("#ready-icon");
const readyTitle = document.querySelector("#ready-title");
const readyDescription = document.querySelector("#ready-description");
const readyUrl = document.querySelector("#ready-url");
const readyUrlWrap = document.querySelector("#ready-url-wrap");
const readyActions = document.querySelector("#ready-actions");
const errorActions = document.querySelector("#error-actions");
const resultHeading = document.querySelector("#result-heading");
const resultEngine = document.querySelector("#result-engine");
const resultFootnote = document.querySelector("#result-footnote");
const openReadyLink = document.querySelector("#open-ready-link");
const copyReadyLink = document.querySelector("#copy-ready-link");
const pasteButton = document.querySelector("#paste-link");
const clearButton = document.querySelector("#clear-link");
const cancelButton = document.querySelector("#cancel-demo");
const resetButton = document.querySelector("#reset-task");
const taskNavLinks = document.querySelectorAll(".task-nav-link");
const securityCheckWrap = document.querySelector("#security-check-wrap");
const turnstileContainer = document.querySelector("#turnstile-widget");
const originalSubmitMarkup = submitButton?.innerHTML || "";
const apiBase = String(window.KIRINDL_CONFIG?.apiBase || "").replace(/\/+$/, "");
const turnstileSiteKey = String(window.KIRINDL_CONFIG?.turnstileSiteKey || "").trim();
let turnstileWidgetId = null;
let turnstileToken = "";
let turnstileWaiters = [];
let challengePending = false;
let activeTaskId = null;
let taskRunId = 0;
let taskRunning = false;
let currentSourceUrl = "";

function setMessage(message, type = "") {
  if (!feedback) return;
  feedback.textContent = message;
  feedback.className = "form-feedback" + (type ? " " + type : "");
}
function settleTurnstileWaiters(error, token = "") {
  const waiters = turnstileWaiters.splice(0);
  waiters.forEach((waiter) => {
    window.clearTimeout(waiter.timer);
    if (error) waiter.reject(error);
    else waiter.resolve(token);
  });
}
function initialiseTurnstile() {
  if (!turnstileSiteKey) return;
  if (!window.turnstile || !turnstileContainer || !securityCheckWrap) {
    throw new Error("Cloudflare security check could not load. Reload the page and try again.");
  }
  securityCheckWrap.hidden = false;
  if (turnstileWidgetId !== null) return;
  turnstileWidgetId = window.turnstile.render(turnstileContainer, {
    sitekey: turnstileSiteKey,
    action: "download",
    theme: "dark",
    size: "compact",
    callback: (token) => {
      turnstileToken = token;
      settleTurnstileWaiters(null, token);
    },
    "expired-callback": () => {
      turnstileToken = "";
      settleTurnstileWaiters(new Error("Security check expired. Complete it again."));
    },
    "error-callback": () => {
      turnstileToken = "";
      settleTurnstileWaiters(new Error("Cloudflare security check failed to load. Try again."));
    }
  });
}
function acquireTurnstileToken() {
  if (!turnstileSiteKey) return Promise.resolve("");
  try {
    initialiseTurnstile();
  } catch (error) {
    return Promise.reject(error);
  }
  if (turnstileToken) return Promise.resolve(turnstileToken);
  setMessage("Complete the Cloudflare security check before starting the download.", "is-info");
  return new Promise((resolve, reject) => {
    const waiter = { resolve, reject, timer: null };
    waiter.timer = window.setTimeout(() => {
      turnstileWaiters = turnstileWaiters.filter((entry) => entry !== waiter);
      reject(new Error("Security check timed out. Complete the check and try again."));
    }, 120000);
    turnstileWaiters.push(waiter);
  });
}
function resetTurnstile() {
  turnstileToken = "";
  if (turnstileWidgetId !== null && window.turnstile) {
    window.turnstile.reset(turnstileWidgetId);
  }
}
function setStage(step, status, className = "") {
  const statusNode = step === "processing" ? processingStatus : mergingStatus;
  const stepNode = step === "processing" ? processingStep : mergingStep;
  statusNode.textContent = status;
  stepNode.classList.remove("is-active", "is-complete");
  if (className) stepNode.classList.add(className);
}
function resetProgress() {
  videoBar.style.width = "0%";
  audioBar.style.width = "0%";
  videoPercent.textContent = "0%";
  audioPercent.textContent = "0%";
  galleryCount.textContent = "0 files collected";
  galleryProgress.hidden = true;
  streamProgressList.hidden = false;
  setStage("processing", "Waiting");
  setStage("merging", "Waiting");
  taskStatus.textContent = "Waiting";
  taskState.textContent = "IDLE";
}
function updateTaskNavigation(visible) {
  taskNavLinks.forEach((link) => { link.hidden = !visible; });
}
function formatBytes(value) {
  if (!Number.isFinite(value) || value < 0) return "";
  if (value < 1024) return value + " B";
  const units = ["KB", "MB", "GB", "TB"];
  let size = value / 1024;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return size.toFixed(1) + " " + units[index];
}
async function apiRequest(path, options = {}) {
  if (!apiBase) {
    throw new Error("Backend belum dikonfigurasi. Jalankan server KirinDL Web Engine dan tetapkan apiBase dalam public/kirindl-config.js.");
  }
  const response = await fetch(apiBase + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  let payload = {};
  try { payload = await response.json(); } catch {}
  if (!response.ok) {
    const detail = payload.detail || payload.message || ("HTTP " + response.status);
    throw new Error(String(detail));
  }
  return payload;
}
function showResultError(message, engineName = "ENGINE") {
  progressPanel.hidden = true;
  downloadsPanel.hidden = false;
  resultHeading.textContent = "Download failed";
  resultEngine.textContent = engineName;
  readyIcon.textContent = "!";
  readyTitle.textContent = "The URL could not be processed";
  readyDescription.textContent = message;
  readyUrlWrap.hidden = true;
  readyActions.hidden = true;
  errorActions.hidden = false;
  resultFootnote.textContent = "Check the URL or selected engine, then try again.";
  taskStatus.textContent = "Failed";
}
function resetToInput(clearUrl = false) {
  taskRunId += 1;
  taskRunning = false;
  activeTaskId = null;
  taskFlow.hidden = true;
  progressPanel.hidden = false;
  downloadsPanel.hidden = true;
  readyUrlWrap.hidden = false;
  readyActions.hidden = false;
  errorActions.hidden = true;
  readyIcon.textContent = "✓";
  mediaInput.disabled = false;
  engineSelect.disabled = false;
  pasteButton.disabled = false;
  clearButton.disabled = false;
  submitButton.disabled = false;
  submitButton.innerHTML = originalSubmitMarkup;
  if (clearUrl) mediaInput.value = "";
  setMessage("Paste a link, choose an engine and start your download.");
  updateTaskNavigation(false);
  resetProgress();
  if (clearUrl) mediaInput.focus();
}
function validateUrl(value) {
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return null;
    return parsed;
  } catch {
    return null;
  }
}
function updateTaskView(task) {
  const progress = task.progress || {};
  const engine = task.engine || engineSelect.value;
  const statusLabels = {
    queued: "Queued",
    downloading: "Downloading",
    processing: "Processing",
    merging: "Merging",
    completed: "Completed",
    failed: "Failed",
    cancelled: "Cancelled"
  };
  taskStatus.textContent = statusLabels[task.status] || task.status;
  taskState.textContent = String(engine).toUpperCase();
  const isGallery = engine === "gallery-dl";
  streamProgressList.hidden = isGallery;
  galleryProgress.hidden = !isGallery;
  if (isGallery) {
    const count = Number(progress.items_completed || 0);
    galleryCount.textContent = count + (count === 1 ? " file collected" : " files collected");
  } else {
    const video = Number(progress.video_percent || 0);
    const audio = Number(progress.audio_percent || 0);
    videoBar.style.width = Math.max(0, Math.min(100, video)) + "%";
    audioBar.style.width = Math.max(0, Math.min(100, audio)) + "%";
    videoPercent.textContent = video + "%";
    audioPercent.textContent = audio + "%";
  }
  if (task.status === "processing" || task.status === "merging" || task.status === "completed") {
    setStage("processing", task.status === "processing" ? "Active" : "Done", task.status === "processing" ? "is-active" : "is-complete");
  }
  if (task.status === "merging" || task.status === "completed") {
    setStage("merging", task.status === "merging" ? "Active" : "Done", task.status === "merging" ? "is-active" : "is-complete");
  }
}
async function pollTask(taskId, runId) {
  let temporaryNetworkErrors = 0;
  while (runId === taskRunId) {
    let task;
    try {
      task = await apiRequest("/api/v1/tasks/" + encodeURIComponent(taskId), { method: "GET", headers: {} });
      temporaryNetworkErrors = 0;
    } catch (error) {
      temporaryNetworkErrors += 1;
      if (temporaryNetworkErrors >= 4) {
        showResultError("Connection to the downloader backend was lost: " + error.message);
        taskRunning = false;
        return;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1200));
      continue;
    }
    updateTaskView(task);
    if (task.status === "completed") {
      progressPanel.hidden = true;
      downloadsPanel.hidden = false;
      resultHeading.textContent = "Download ready";
      resultEngine.textContent = String(task.engine || "Engine").toUpperCase();
      readyIcon.textContent = "✓";
      readyTitle.textContent = "Your file is ready";
      const countText = task.file_count > 1 ? task.file_count + " files bundled" : "1 file";
      const sizeText = Number.isFinite(task.file_size) ? " · " + formatBytes(task.file_size) : "";
      readyDescription.textContent = countText + sizeText + ". Download the output below.";
      readyUrl.textContent = task.filename || "KirinDL output";
      readyUrlWrap.hidden = false;
      readyActions.hidden = false;
      errorActions.hidden = true;
      openReadyLink.href = apiBase + task.download_url;
      openReadyLink.textContent = "Download file";
      openReadyLink.setAttribute("download", "");
      resultFootnote.textContent = "After you start the file download, this panel will close and return to the URL input.";
      taskRunning = false;
      return;
    }
    if (task.status === "failed") {
      showResultError(task.error || "The engine could not process this URL.", String(task.engine || "ENGINE").toUpperCase());
      taskRunning = false;
      return;
    }
    if (task.status === "cancelled") {
      resetToInput(false);
      setMessage("Download task cancelled.", "is-info");
      return;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
  }
}
async function startTask(url, engine, challengeToken = "") {
  if (!apiBase) {
    setMessage("Backend belum dikonfigurasi. Jalankan KirinDL Web Engine dan tetapkan apiBase dalam public/kirindl-config.js.", "is-error");
    return;
  }
  const runId = ++taskRunId;
  taskRunning = true;
  currentSourceUrl = url;
  taskFlow.hidden = false;
  progressPanel.hidden = false;
  downloadsPanel.hidden = true;
  updateTaskNavigation(true);
  resetProgress();
  taskUrl.textContent = url;
  taskStatus.textContent = "Queued";
  taskState.textContent = engine.toUpperCase();
  mediaInput.disabled = true;
  engineSelect.disabled = true;
  pasteButton.disabled = true;
  clearButton.disabled = true;
  submitButton.disabled = true;
  submitButton.textContent = "Submitting…";
  setMessage("Sending the URL to the selected server-side engine…", "is-info");
  try {
    const task = await apiRequest("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify({ url, engine, challenge_token: challengeToken || null })
    });
    resetTurnstile();
    if (runId !== taskRunId) return;
    activeTaskId = task.id;
    updateTaskView(task);
    submitButton.textContent = "Downloading…";
    await pollTask(task.id, runId);
  } catch (error) {
    resetTurnstile();
    if (runId !== taskRunId) return;
    taskRunning = false;
    mediaInput.disabled = false;
    engineSelect.disabled = false;
    pasteButton.disabled = false;
    clearButton.disabled = false;
    submitButton.disabled = false;
    submitButton.innerHTML = originalSubmitMarkup;
    taskFlow.hidden = true;
    updateTaskNavigation(false);
    setMessage(error.message, "is-error");
  }
}
pasteButton?.addEventListener("click", async () => {
  if (!navigator.clipboard?.readText) {
    setMessage("Clipboard access is unavailable. Paste the link into the field manually.", "is-error");
    mediaInput.focus();
    return;
  }
  try {
    const value = await navigator.clipboard.readText();
    if (!value.trim()) {
      setMessage("Your clipboard is empty.", "is-info");
      return;
    }
    mediaInput.value = value.trim();
    setMessage("Link pasted. Choose an engine and start the download.", "is-info");
  } catch {
    setMessage("Clipboard permission was not granted. You can paste the link manually.", "is-error");
  }
});
clearButton?.addEventListener("click", () => {
  if (taskRunning) return;
  mediaInput.value = "";
  setMessage("URL cleared.");
  mediaInput.focus();
});
form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (taskRunning || challengePending) return;
  const value = mediaInput.value.trim();
  if (!value) {
    setMessage("Enter a media URL first.", "is-error");
    mediaInput.focus();
    return;
  }
  const parsed = validateUrl(value);
  if (!parsed) {
    setMessage("Enter a valid http:// or https:// URL.", "is-error");
    mediaInput.focus();
    return;
  }
  challengePending = true;
  submitButton.disabled = true;
  try {
    const challengeToken = await acquireTurnstileToken();
    challengePending = false;
    submitButton.disabled = false;
    await startTask(parsed.href, engineSelect.value, challengeToken);
  } catch (error) {
    challengePending = false;
    submitButton.disabled = false;
    setMessage(error.message, "is-error");
  }
});
cancelButton?.addEventListener("click", async () => {
  const id = activeTaskId;
  if (id) {
    try { await apiRequest("/api/v1/tasks/" + encodeURIComponent(id), { method: "DELETE", headers: {} }); } catch {}
  }
  resetToInput(false);
  setMessage("Download cancelled. Your URL is still in the input field.", "is-info");
  mediaInput.focus();
});
copyReadyLink?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(currentSourceUrl);
    setMessage("Source URL copied.", "is-info");
  } catch {
    setMessage("Clipboard access is unavailable.", "is-error");
  }
});
openReadyLink?.addEventListener("click", () => {
  window.setTimeout(() => resetToInput(true), 1500);
});
resetButton?.addEventListener("click", () => resetToInput(false));

if (turnstileSiteKey) {
  try {
    initialiseTurnstile();
  } catch (error) {
    setMessage(error.message, "is-error");
  }
}
