/* Public frontend configuration. Do not put secrets or shared API tokens here. */
(() => {
  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  window.KIRINDL_CONFIG = Object.freeze({
    apiBase: isLocal ? "http://127.0.0.1:8000" : ""
  });
})();
