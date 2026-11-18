import { renderHomePage } from '../pages/home/index.js';
import { renderDownloadPage } from '../pages/download/index.js';
import { renderHistoryPage } from '../pages/history/index.js';
import { renderSettingsPage } from '../pages/settings/index.js';
import { renderToolsPage } from '../pages/tools/index.js';

const routes = {
  home: renderHomePage,
  download: renderDownloadPage,
  history: renderHistoryPage,
  settings: renderSettingsPage,
  tools: renderToolsPage
};

export function startRouter(target) {
  if (!target) {
    throw new Error('The page view mount point was not found.');
  }

  function renderRoute() {
    const requestedRoute = window.location.hash.replace(/^#\/?/, '').split('/')[0];
    const route = routes[requestedRoute] ? requestedRoute : 'home';
    target.innerHTML = routes[route]();
    document.querySelectorAll('[data-route]').forEach((link) => {
      const active = link.dataset.route === route;
      link.classList.toggle('is-active', active);
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }

  window.addEventListener('hashchange', renderRoute);
  renderRoute();
}
