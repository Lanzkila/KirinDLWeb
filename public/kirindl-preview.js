const menuButton = document.querySelector("#menu-trigger");
const menuPanel = document.querySelector("#site-menu");
const resumeLink = document.querySelector("[data-resume-link]");
const resumeLabel = document.querySelector("[data-resume-label]");
const lastPageKey = "kirindl-web-preview:last-page";
const allowedPages = new Map([
  ["#top", "Home"], ["#downloader", "Downloader"], ["#progress", "Progress"],
  ["#downloads", "Downloads"], ["pages/contact.html", "Contact"],
  ["pages/support.html", "Support"], ["pages/issues.html", "Issues"],
  ["pages/privacy.html", "Privacy"]
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
  if (pageLink) { rememberPage(pageLink); closeMenu(); }
  if (menuPanel && !menuPanel.hidden && !event.target.closest(".menu-wrap")) closeMenu();
});
resumeLink?.addEventListener("click", closeMenu);
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeMenu(); });
updateResume();

const mediaInput = document.querySelector("#media-url");
const feedback = document.querySelector("#form-feedback");
const engineSelect = document.querySelector("#engine-select");
document.querySelector("#paste-link")?.addEventListener("click", async () => {
  if (!navigator.clipboard?.readText) {
    feedback.textContent = "Clipboard access is unavailable. Paste the link into the field manually.";
    feedback.className = "form-feedback is-error";
    mediaInput.focus();
    return;
  }
  try {
    const clipboardText = await navigator.clipboard.readText();
    if (!clipboardText.trim()) {
      feedback.textContent = "Your clipboard is empty.";
      feedback.className = "form-feedback is-info";
      return;
    }
    mediaInput.value = clipboardText.trim();
    feedback.textContent = "Link pasted. Press Analyse link to check its URL format.";
    feedback.className = "form-feedback is-info";
  } catch {
    feedback.textContent = "Clipboard permission was not granted. You can paste the link manually.";
    feedback.className = "form-feedback is-error";
  }
});
document.querySelector("#clear-link")?.addEventListener("click", () => {
  mediaInput.value = "";
  feedback.textContent = "URL cleared. No task has been started.";
  feedback.className = "form-feedback";
  mediaInput.focus();
});
document.querySelector("#download-form")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = mediaInput.value.trim();
  if (!value) {
    feedback.textContent = "Enter a media URL first.";
    feedback.className = "form-feedback is-error";
    mediaInput.focus();
    return;
  }
  let parsed;
  try { parsed = new URL(value); } catch {
    feedback.textContent = "That does not look like a valid URL. Check the link and try again.";
    feedback.className = "form-feedback is-error";
    mediaInput.focus();
    return;
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    feedback.textContent = "Only http:// and https:// links can be entered.";
    feedback.className = "form-feedback is-error";
    mediaInput.focus();
    return;
  }
  const engineName = engineSelect.selectedOptions[0]?.textContent || "Auto detect";
  feedback.textContent = "URL format looks valid. Selected engine: " + engineName + ". The web downloader is not connected yet, so no analysis or download was started.";
  feedback.className = "form-feedback is-info";
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
    document.querySelectorAll("[data-auth-form]").forEach((form) => { form.hidden = form.dataset.authForm !== mode; });
    authTitle.textContent = mode === "login" ? "Welcome back" : "Create your account";
    authFeedback.textContent = "Account authentication is not connected yet. This form is for layout preview only.";
  });
});
document.querySelectorAll("[data-auth-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (form.dataset.authForm === "register") {
      const password = form.querySelector('[name="password"]');
      const confirmPassword = form.querySelector('[name="confirm"]');
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
