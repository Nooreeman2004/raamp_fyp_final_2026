import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/services/api';

type Place = {
  place_id: string;
  name: string;
  formatted_address?: string;
  lat?: number;
  lng?: number;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onConnected: (payload: { place_id: string; name: string; formatted_address?: string; lat?: number; lng?: number }) => void;
};

export default function MapsConnectModal({ isOpen, onClose, onConnected }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Place | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [pickerReady, setPickerReady] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const loaderRef = useRef<HTMLElement | null>(null);
  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults([]);
      setSelected(null);
      setPickerReady(false);
    }
    // when modal opens, if Google key present, ensure the extended component lib is loaded
    if (isOpen && GOOGLE_KEY) {
      // inject script if not present
      const scriptId = 'gmpx-extended-lib';
      if (!document.getElementById(scriptId)) {
        const s = document.createElement('script');
        s.type = 'module';
        s.src = 'https://ajax.googleapis.com/ajax/libs/@googlemaps/extended-component-library/0.6.11/index.min.js';
        s.id = scriptId;
        document.head.appendChild(s);
      }
    }
  }, [isOpen, GOOGLE_KEY]);

  // When Google key present, configure loader and wire up the place-picker change event
  useEffect(() => {
    if (!isOpen || !GOOGLE_KEY) return;

    let mounted = true;
    let cleanupFn: (() => void) | undefined;

    const configure = async () => {
      // wait for the extended lib to define custom elements
      const waitFor = (name: string, timeout = 5000) => new Promise<boolean>((resolve) => {
        const start = Date.now();
        const tick = () => {
          if ((window as any).customElements && (window as any).customElements.get(name)) return resolve(true);
          if (Date.now() - start > timeout) return resolve(false);
          setTimeout(tick, 150);
        };
        tick();
      });

      const ok = await waitFor('gmpx-place-picker', 8000);
      if (!mounted) return;
      setPickerReady(ok);

      // If GMPX didn't register in time, attempt a graceful fallback by loading
      // the Google Maps JS API with the Places library so the page can still
      // provide a search + selection UX.
      if (!ok) {
        console.error('GMPX place-picker did not register within timeout. Falling back to Google Maps JS API loader.');
        try {
          if (!document.getElementById('google-maps-js')) {
            (window as any).__raamp_gmaps_loaded = false;
            (window as any).__raamp_gmaps_error = false;
            (window as any).__raamp_init_maps = () => { (window as any).__raamp_gmaps_loaded = true; };
            const s = document.createElement('script');
            s.id = 'google-maps-js';
            s.async = true;
            s.defer = true;
            s.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_KEY}&libraries=places&callback=__raamp_init_maps`;
            s.onerror = () => { (window as any).__raamp_gmaps_error = true; console.error('Failed to load Google Maps JS API fallback'); };
            document.head.appendChild(s);
            // wait briefly for load to complete
            const start = Date.now();
            while (Date.now() - start < 6000 && !(window as any).__raamp_gmaps_loaded && !(window as any).__raamp_gmaps_error) {
              // eslint-disable-next-line no-await-in-loop
              await new Promise((r) => setTimeout(r, 150));
            }
            if ((window as any).__raamp_gmaps_loaded) console.info('Google Maps JS API loaded (fallback)');
            else console.warn('Google Maps JS API fallback did not finish loading');
          }
        } catch (e) {
          console.error('Error while loading Google Maps fallback', e);
        }
      }

      // set loader attributes (use correct attribute name expected by gmpx-api-loader)
      if (loaderRef.current) {
        try {
          // Give the loader the API key and request the Places library.
          loaderRef.current.setAttribute('api-key', GOOGLE_KEY);
          loaderRef.current.setAttribute('libraries', 'places');
          loaderRef.current.setAttribute('solution-channel', 'GMP_GE_placepicker_v2');
          // Disable auto-init to allow the app to wire events explicitly.
          loaderRef.current.setAttribute('auto-init', 'false');
          loaderRef.current.setAttribute('autoinit', 'false');
        } catch (e) {
          console.error('Failed to configure gmpx-api-loader', e);
        }
      }

      const placePicker = containerRef.current?.querySelector('gmpx-place-picker') as HTMLElement | null;
      const markerEl = containerRef.current?.querySelector('gmp-advanced-marker') as any | null;

      const onPlaceChange = () => {
        try {
          const picker = placePicker as any;
          const place = picker?.value || {};
          if (!place) return;

          // extract common fields from different shapes returned by the component
          const place_id = place.placeId || place.place_id || place.placeIdString || place.placeIdValue;
          const name = place.displayName || place.name || place.poiName || '';
          const formatted_address = place.formattedAddress || place.formatted_address || place.address || '';

          // robust coordinate extraction
          let lat: number | undefined = undefined;
          let lng: number | undefined = undefined;
          if (place.location) {
            const loc = place.location;
            if (typeof loc.lat === 'function' && typeof loc.lng === 'function') {
              lat = loc.lat(); lng = loc.lng();
            } else if (typeof loc.lat === 'number' && typeof loc.lng === 'number') {
              lat = loc.lat; lng = loc.lng;
            } else if (Array.isArray(loc) && loc.length >= 2) {
              lat = Number(loc[0]); lng = Number(loc[1]);
            }
          }

          // set marker position if available
          try {
            if (markerEl && place.location) {
              markerEl.position = place.location;
            }
          } catch (e) {
            // ignore
          }

          setSelected({
            place_id: place_id || String(Math.random()).slice(2),
            name: name || 'Selected place',
            formatted_address,
            lat,
            lng,
          });
        } catch (e) {
          console.error('placechange handler error', e);
        }
      };

      if (placePicker) {
        placePicker.addEventListener('gmpx-placechange', onPlaceChange);
        // Return cleanup function
        return () => {
          placePicker.removeEventListener('gmpx-placechange', onPlaceChange);
        };
      }
    };

    configure().then((c) => { 
      if (typeof c === 'function') cleanupFn = c;
    }).catch(() => {});

    return () => { 
      mounted = false;
      if (cleanupFn) cleanupFn(); 
    };
  }, [isOpen, GOOGLE_KEY]);

  const doSearch = async (q: string) => {
    if (!q || q.trim().length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      // Use onboarding maps search endpoint
      const res: any = await apiClient.post('/profile/onboarding/maps/search', { query: q.trim() });
      // expect res.data.results or res.results depending on client adapter
      setResults((res && (res.data?.results || res.results)) || []);
    } catch (err: any) {
      console.error('Search error', err);
      alert('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDetails = async (place_id: string) => {
    setDetailsLoading(true);
    try {
      // Use onboarding maps confirm endpoint to get canonical details
      const res: any = await apiClient.post('/profile/onboarding/maps/confirm', { place_id });
      const data = res && (res.data || res);
      setSelected({
        place_id: data.place_id,
        name: data.name,
        formatted_address: data.formatted_address || data.address,
        lat: data.lat,
        lng: data.lng,
      });
    } catch (err: any) {
      console.error('Details error', err);
      alert('Failed to load place details');
    } finally {
      setDetailsLoading(false);
    }
  };

  const confirm = async () => {
    if (!selected) return;
    try {
      const payload = {
        place_id: selected.place_id,
        name: selected.name,
        address: selected.formatted_address,
      };
      // Save via maps save endpoint in onboarding router
      await apiClient.post('/profile/onboarding/maps/save', payload);
      onConnected({ ...payload, formatted_address: selected.formatted_address, lat: selected.lat, lng: selected.lng });
      onClose();
    } catch (err: any) {
      console.error('Connect error', err);
      alert('Failed to connect place. Please try again.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card p-6 rounded-lg w-full max-w-2xl" ref={containerRef}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Connect Google Maps</h3>
          <Button variant="ghost" onClick={onClose}>Close</Button>
        </div>
        {!selected && (
          <div>
            {/* If Google key present AND the GMPX place picker loaded, render the client-side UI.
                Otherwise, fall back to the backend-powered search list so users always see a search box. */}
            {GOOGLE_KEY && pickerReady ? (
              <div>
                {/* gmpx loader and map/place-picker are custom elements; set loader attributes after mount */}
                <gmpx-api-loader ref={(el) => { loaderRef.current = el as any; }}></gmpx-api-loader>
                <div className="mb-3">
                  <gmp-map center="40.749933,-73.98633" zoom="13" map-id="DEMO_MAP_ID">
                    <div slot="control-block-start-inline-start" className="place-picker-container">
                      <gmpx-place-picker placeholder="Search for your business"></gmpx-place-picker>
                    </div>
                    <gmp-advanced-marker></gmp-advanced-marker>
                  </gmp-map>
                  <style>{`
                    gmp-map {
                      display: block;
                      width: 100%;
                      min-height: 320px;
                      border-radius: 8px;
                      overflow: hidden;
                    }
                    gmpx-place-picker, gmpx-place-picker input, .place-picker-container { z-index: 9999 !important; }
                    .place-picker-container { position: relative; }
                    gmpx-place-picker .gmpx-search-box { z-index: 10000 !important; }
                  `}</style>
                </div>
                <div className="text-sm text-muted-foreground">Use the search box on the map to pick your business. After selection, confirm below.</div>
              </div>
            ) : (
              <div>
                <div className="flex gap-2 mb-4">
                  <input
                    className="flex-1 input"
                    placeholder="Search for your business (e.g. 'Corner Cafe')"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      doSearch(e.target.value);
                    }}
                  />
                  <Button onClick={() => doSearch(query)} disabled={loading}>Search</Button>
                </div>

                <div className="space-y-2 max-h-64 overflow-auto">
                  {loading && <div>Searching…</div>}
                  {!loading && results.length === 0 && <div className="text-sm text-muted-foreground">No results</div>}
                  {results.map((r) => (
                    <div key={r.place_id} className="p-3 bg-muted/50 rounded flex justify-between items-center">
                      <div>
                        <div className="font-semibold">{r.name}</div>
                        <div className="text-sm text-muted-foreground">{r.formatted_address}</div>
                      </div>
                      <div>
                        <Button size="sm" onClick={() => fetchDetails(r.place_id)}>Select</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {selected && (
          <div>
            <h4 className="font-semibold mb-2">Confirm Location</h4>
            <div className="mb-3">
              <div className="font-bold">{selected.name}</div>
              <div className="text-sm text-muted-foreground">{selected.formatted_address}</div>
            </div>

            {/* Map preview: use OpenStreetMap iframe as a lightweight Leaflet-free fallback */}
            {selected.lat && selected.lng ? (
              <div className="mb-3 w-full h-56">
                <iframe
                  title="map-preview"
                  width="100%"
                  height="100%"
                  frameBorder={0}
                  src={`https://www.openstreetmap.org/export/embed.html?bbox=${selected.lng - 0.002}%2C${selected.lat - 0.002}%2C${selected.lng + 0.002}%2C${selected.lat + 0.002}&layer=mapnik&marker=${selected.lat}%2C${selected.lng}`}
                />
                <div className="text-xs text-muted-foreground mt-1">Map preview (OpenStreetMap)</div>
              </div>
            ) : (
              <div className="mb-3 text-sm text-muted-foreground">No coordinates available for preview.</div>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setSelected(null)}>Back</Button>
              <Button onClick={confirm} disabled={detailsLoading}>This is my business</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}