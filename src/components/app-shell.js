export function mountAppShell(root) {
  root.className = 'app-shell';
  root.innerHTML = `
    <header class="topbar">
      <a class="brand" href="#/home" aria-label="KirinDL Web home">
        <span class="brand-mark">K</span>
        <span>Kirin<span class="brand-accent">DL</span><small>WEB PLATFORM</small></span>
      </a>
      <span class="platform-label">Independent web client</span>
    </header>
    <div class="workspace">
      <aside class="sidebar" aria-label="Main navigation">
        <span class="nav-caption">WORKSPACE</span>
        <nav>
          <a data-route="home" href="#/home">Overview</a>
          <a data-route="download" href="#/download">Downloader</a>
          <a data-route="history" href="#/history">History</a>
          <a data-route="tools" href="#/tools">Tools</a>
          <a data-route="settings" href="#/settings">Settings</a>
        </nav>
        <div class="sidebar-note">
          <span class="status-dot"></span>
          <span>Scaffold preview<small>Core services not connected</small></span>
        </div>
      </aside>
      <main id="page-view" class="page-view" tabindex="-1"></main>
    </div>
    <footer class="footer">
      <span>KirinDL Web</span>
      <span>Separate platform · Shared project identity</span>
      <a href="https://github.com/Lanzkila/KirinDL">Android project</a>
    </footer>
  `;
}
