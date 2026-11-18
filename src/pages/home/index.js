export function renderHomePage() {
  return `
    <section class="page-heading">
      <p class="eyebrow">KIRINDL / WEB</p>
      <h1>Media in motion.<br><span>Downloads in control.</span></h1>
      <p class="lead">A dedicated web workspace designed to work alongside the KirinDL Android app.</p>
    </section>
    <section class="notice-card">
      <span class="notice-icon">i</span>
      <div><strong>Development scaffold</strong><p>This is the initial web structure. Download extraction, history sync, backend services and the Android bridge are not connected yet.</p></div>
    </section>
    <section class="feature-grid">
      <a class="feature-card" href="#/download"><span class="feature-symbol">↓</span><strong>Downloader</strong><p>URL input and format selection will live here.</p><span class="card-link">Open workspace ↗</span></a>
      <a class="feature-card" href="#/history"><span class="feature-symbol">◷</span><strong>History</strong><p>Web download records and future sync status.</p><span class="card-link">View history ↗</span></a>
      <a class="feature-card" href="#/tools"><span class="feature-symbol">✳</span><strong>Tools</strong><p>Browser-compatible utilities and media helpers.</p><span class="card-link">Explore tools ↗</span></a>
    </section>
    <section class="section-heading"><div><p class="eyebrow">PLATFORM DESIGN</p><h2>Two platforms, one project</h2></div></section>
    <p class="body-copy">The Android app keeps its native engines and device features. The web client will use browser-compatible services and a separately deployed backend where required. A documented bridge will connect supported actions between them.</p>
  `;
}
