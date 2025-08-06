// src/utils/externalScripts.js

let scriptsLoaded = false;
let loadPromise = null;

function loadScript(src) {
  return new Promise((resolve, reject) => {
    // Check if the script is already in the document.
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    // Do not use async or defer to ensure immediate execution.
    script.async = false;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

export function loadExternalScripts() {
  if (scriptsLoaded) {
    return Promise.resolve();
  }
  if (!loadPromise) {
    loadPromise = (async () => {
      await loadScript("https://cdn.plaid.com/link/v2/stable/link-initialize.js");
      await loadScript("https://cdn.teller.io/connect/connect.js");
      scriptsLoaded = true;
      console.log("External scripts loaded");
    })();
  }
  return loadPromise;
}
