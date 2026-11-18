/* Public frontend configuration. Never put server secrets or shared API tokens here. */
(() => {
  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  window.KIRINDL_CONFIG = Object.freeze({
    apiBase: isLocal ? "http://127.0.0.1:8000" : "",
    // Public Cloudflare Turnstile sitekey only. Keep the secret in the backend .env.
    turnstileSiteKey: ""
  });
})();
