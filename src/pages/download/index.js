export function renderDownloadPage() {
  return `
    <section class="page-heading compact">
      <p class="eyebrow">WORKSPACE / DOWNLOAD</p>
      <h1>Downloader</h1>
      <p class="lead">The web download flow will be implemented here.</p>
    </section>
    <section class="panel">
      <label class="field-label" for="media-url">Media URL</label>
      <div class="input-row"><input id="media-url" type="url" placeholder="https://…" disabled><button type="button" disabled>Inspect URL</button></div>
      <p class="muted">URL inspection and extraction are not connected in this scaffold.</p>
    </section>
    <section class="panel panel-subtle">
      <strong>Planned flow</strong>
      <ol><li>Submit a supported URL.</li><li>Retrieve metadata and available formats.</li><li>Choose the output and start a web-compatible task.</li><li>Track progress or hand the request to the Android app.</li></ol>
    </section>
  `;
}
