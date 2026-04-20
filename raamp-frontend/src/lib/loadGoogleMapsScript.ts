/**
 * Single Google Maps JavaScript API load for the whole SPA.
 * One script tag with a fixed ?libraries= list avoids loading Maps twice with different
 * libraries (which corrupts global state and causes undefined errors).
 */
const SCRIPT_ID = "google-maps-api-script";

/** Libraries required app-wide — keep in sync with components that use Maps. */
const LIBRARIES = ["places", "visualization"] as const;

let loadPromise: Promise<void> | null = null;

function mapsReady(): boolean {
  return typeof window !== "undefined" && !!(window as unknown as { google?: { maps?: unknown } }).google?.maps;
}

export function loadGoogleMapsScript(apiKey: string): Promise<void> {
  const key = apiKey.trim();
  if (!key) {
    return Promise.reject(new Error("Missing VITE_GOOGLE_MAPS_API_KEY"));
  }

  if (mapsReady()) {
    return Promise.resolve();
  }

  if (loadPromise) {
    return loadPromise;
  }

  loadPromise = new Promise<void>((resolve, reject) => {
    const done = () => {
      if (mapsReady()) resolve();
      else reject(new Error("Google Maps API did not initialize"));
    };

    const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (existing) {
      if (mapsReady()) {
        done();
        return;
      }
      const onErr = () => {
        loadPromise = null;
        reject(new Error("Google Maps script error"));
      };
      existing.addEventListener("load", done, { once: true });
      existing.addEventListener("error", onErr, { once: true });
      // Script may have finished loading before we subscribed
      queueMicrotask(() => {
        if (mapsReady()) done();
      });
      return;
    }

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    const libs = LIBRARIES.join(",");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&libraries=${libs}`;
    script.async = true;
    script.defer = true;
    script.onload = () => done();
    script.onerror = () => {
      loadPromise = null;
      reject(new Error("Failed to load Google Maps JavaScript API"));
    };
    document.head.appendChild(script);
  });

  return loadPromise;
}
