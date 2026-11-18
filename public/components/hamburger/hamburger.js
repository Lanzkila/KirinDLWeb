/* Hamburger navigation */
const menuButton = document.querySelector("#menu-trigger");
const menuPanel = document.querySelector("#site-menu");

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
  if (event.target.closest(".menu-links a")) closeMenu();
  if (menuPanel && !menuPanel.hidden && !event.target.closest(".menu-wrap")) closeMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMenu();
});
