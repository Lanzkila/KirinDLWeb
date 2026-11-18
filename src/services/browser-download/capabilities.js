export function getBrowserDownloadCapabilities() {
  return {
    blobDownload: typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function',
    fileSystemAccess: typeof window !== 'undefined' && 'showSaveFilePicker' in window,
    serviceWorker: typeof navigator !== 'undefined' && 'serviceWorker' in navigator
  };
}
