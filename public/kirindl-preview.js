const menuButton = document.querySelector("#menu-trigger");
const menuPanel = document.querySelector("#site-menu");
const resumeLink = document.querySelector("[data-resume-link]");
const resumeLabel = document.querySelector("[data-resume-label]");
const lastPageKey = "kirindl-web-preview:last-page";
const allowedPages = new Map([
  ["#top", "Home"], ["#downloader", "Downloader"],
  ["pages/contact.html", "Contact"], ["pages/support.html", "Support"],
  ["pages/issues.html", "Issues"], ["pages/privacy.html", "Privacy"]
]);

function readLastPage() {
  try {
    const saved = JSON.parse(localStorage.getItem(lastPageKey) || "null");
    if (!saved || !allowedPages.has(saved.href)) return null;
    return { href: saved.href, label: allowedPages.get(saved.href) };
  } catch { return null; }
}
function updateResume() {
  const target = readLastPage() || { href: "#downloader", label: "Downloader" };
  resumeLink.href = target.href;
  resumeLabel.textContent = target.label;
}
function rememberPage(link) {
  const href = link.getAttribute("href");
  if (!allowedPages.has(href)) return;
  try { localStorage.setItem(lastPageKey, JSON.stringify({ href: href, label: allowedPages.get(href) })); } catch {}
  updateResume();
}
function closeMenu() {
  if (!menuButton || !menuPanel) return;
  menuPanel.hidden = true;
  menuButton.setAttribute("aria-expanded", "false");
}
function openMenu() {
  if (!menuButton || !menuPanel) return;
  menuPanel.hidden = false;
  menuButton.setAttribute("aria-expanded", "true");
}
menuButton?.addEventListener("click", () => menuPanel.hidden ? openMenu() : closeMenu());
document.addEventListener("click", (event) => {
  const pageLink = event.target.closest("[data-page-link]");
  if (pageLink) rememberPage(pageLink);
  if (event.target.closest(".menu-links a, [data-resume-link]")) closeMenu();
  if (menuPanel && !menuPanel.hidden && !event.target.closest(".menu-wrap")) closeMenu();
});
resumeLink?.addEventListener("click", closeMenu);
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeMenu(); });
updateResume();

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
const processingStep = document.querySelector("#processing-step");
const mergingStep = document.querySelector("#merging-step");
const processingStatus = document.querySelector("#processing-status");
const mergingStatus = document.querySelector("#merging-status");
const readyUrl = document.querySelector("#ready-url");
const openReadyLink = document.querySelector("#open-ready-link");
const taskNavLinks = document.querySelectorAll(".task-nav-link");
const originalSubmitMarkup = submitButton.innerHTML;
let taskRunId = 0;
let taskRunning = false;

function setMessage(message, type) {
  feedback.textContent = message;
  feedback.className = "form-feedback" + (type ? " " + type : "");
}
function setStage(step, status, className) {
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
  setStage("processing", "Waiting", "");
  setStage("merging", "Waiting", "");
  taskStatus.textContent = "Waiting";
  taskState.textContent = "IDLE";
}
function animateBar(bar, label, duration, runId) {
  return new Promise((resolve) => {
    const started = performance.now();
    function frame(now) {
      if (runId !== taskRunId) { resolve(false); return; }
      const percent = Math.min(100, Math.round(((now - started) / duration) * 100));
      bar.style.width = percent + "%";
      label.textContent = percent + "%";
      if (percent >= 100) resolve(true);
      else requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  });
}
function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
function updateTaskNavigation(isVisible) {
  taskNavLinks.forEach((link) => { link.hidden = !isVisible; });
}
function resetToInput(clearUrl) {
  taskRunId += 1;
  taskRunning = false;
  taskFlow.hidden = true;
  progressPanel.hidden = false;
  downloadsPanel.hidden = true;
  document.body.classList.remove("has-task");
  updateTaskNavigation(false);
  resetProgress();
  mediaInput.disabled = false;
  engineSelect.disabled = false;
  document.querySelector("#paste-link").disabled = false;
  submitButton.disabled = false;
  submitButton.innerHTML = originalSubmitMarkup;
  if (clearUrl) mediaInput.value = "";
  setMessage("Paste a link and press Analyse link to start the preview flow.", "");
  if (clearUrl) mediaInput.focus();
}
function validateUrl(value) {
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
    return parsed;
  } catch { return null; }
}
async function startPreviewFlow(url, engineName) {
  const runId = ++taskRunId;
  taskRunning = true;
  taskFlow.hidden = false;
  progressPanel.hidden = false;
  downloadsPanel.hidden = true;
  document.body.classList.add("has-task");
  updateTaskNavigation(true);
  resetProgress();
  taskUrl.textContent = url;
  taskStatus.textContent = "Downloading";
  taskState.textContent = engineName.toUpperCase().replace(/[^A-Z0-9]+/g, "-");
  mediaInput.disabled = true;
  engineSelect.disabled = true;
  document.querySelector("#paste-link").disabled = true;
  submitButton.disabled = true;
  submitButton.textContent = "Processing…";
  setMessage("Preview sequence started. The percentages below are simulated, not real downloads.", "is-info");

  const streamsDone = await Promise.all([
    animateBar(videoBar, videoPercent, 2600, runId),
    animateBar(audioBar, audioPercent, 2200, runId)
  ]);
  if (runId !== taskRunId || streamsDone.some((done) => !done)) return;

  taskStatus.textContent = "Processing";
  taskState.textContent = "PROCESS";
  setStage("processing", "Active", "is-active");
  await wait(1100);
  if (runId !== taskRunId) return;
  setStage("processing", "Done", "is-complete");

  taskStatus.textContent = "Merging";
  taskState.textContent = "MERGE";
  setStage("merging", "Active", "is-active");
  await wait(1100);
  if (runId !== taskRunId) return;
  setStage("merging", "Done", "is-complete");
  taskStatus.textContent = "Ready";
  taskState.textContent = "DONE";

  progressPanel.hidden = true;
  downloadsPanel.hidden = false;
  readyUrl.textContent = url;
  openReadyLink.href = url;
  setMessage("Preview flow finished. The submitted link has been placed in the Downloads area temporarily.", "is-info");
  await wait(4800);
  if (runId !== taskRunId) return;
  resetToInput(true);
}

document.querySelector("#paste-link")?.addEventListener("click", async () => {
  if (!navigator.clipboard?.readText) {
    setMessage("Clipboard access is unavailable. Paste the link into the field manually.", "is-error");
    mediaInput.focus();
    return;
  }
  try {
    const value = await navigator.clipboard.readText();
    if (!value.trim()) { setMessage("Your clipboard is empty.", "is-info"); return; }
    mediaInput.value = value.trim();
    setMessage("Link pasted. Press Analyse link to start.", "is-info");
  } catch {
    setMessage("Clipboard permission was not granted. You can paste the link manually.", "is-error");
  }
});
document.querySelector("#clear-link")?.addEventListener("click", () => {
  if (taskRunning) resetToInput(false);
  mediaInput.value = "";
  setMessage("URL cleared.", "");
  mediaInput.focus();
});
form?.addEventListener("submit", (event) => {
  event.preventDefault();
  if (taskRunning) return;
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
  const engineName = engineSelect.selectedOptions[0]?.textContent || "Auto detect";
  startPreviewFlow(parsed.href, engineName);
});
document.querySelector("#cancel-demo")?.addEventListener("click", () => {
  resetToInput(false);
  setMessage("Preview cancelled. Your link is still in the input field.", "is-info");
  mediaInput.focus();
});
document.querySelector("#copy-ready-link")?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(readyUrl.textContent);
    setMessage("Submitted link copied. Returning to the input screen shortly.", "is-info");
  } catch {
    setMessage("Clipboard access is unavailable. You can select and copy the displayed link.", "is-error");
  }
});

const accountDialog = document.querySelector("#account-dialog");
const authFeedback = document.querySelector("#auth-feedback");
const authTitle = document.querySelector("#account-title");
document.querySelector("#account-trigger")?.addEventListener("click", () => {
  if (typeof accountDialog.showModal === "function") accountDialog.showModal();
  else accountDialog.setAttribute("open", "");
});
document.querySelector("[data-dialog-close]")?.addEventListener("click", () => {
  if (typeof accountDialog.close === "function") accountDialog.close();
  else accountDialog.removeAttribute("open");
});
document.querySelectorAll("[data-auth-tab]").forEach((tab) => {
  tab.addEventListener("click", () => {
    const mode = tab.dataset.authTab;
    document.querySelectorAll("[data-auth-tab]").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll("[data-auth-form]").forEach((authForm) => { authForm.hidden = authForm.dataset.authForm !== mode; });
    authTitle.textContent = mode === "login" ? "Welcome back" : "Create your account";
    authFeedback.textContent = "Account authentication is not connected yet. This form is for layout preview only.";
  });
});
document.querySelectorAll("[data-auth-form]").forEach((authForm) => {
  authForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (authForm.dataset.authForm === "register") {
      const password = authForm.querySelector('[name="password"]');
      const confirmPassword = authForm.querySelector('[name="confirm"]');
      if (password.value !== confirmPassword.value) {
        authFeedback.textContent = "The passwords do not match.";
        confirmPassword.setCustomValidity("Passwords do not match.");
        confirmPassword.reportValidity();
        return;
      }
      confirmPassword.setCustomValidity("");
    }
    authFeedback.textContent = "This is a visual prototype only. Authentication is not connected, and no credentials were sent or saved.";
  });
});
