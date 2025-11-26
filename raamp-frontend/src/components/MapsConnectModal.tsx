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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const loaderRef = useRef<HTMLElement | null>(null);
  const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults([]);
      setSelected(null);
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
  }, [isOpen]);

  // When Google key present, configure loader and wire up the place-picker change event
  useEffect(() => {
    if (!isOpen || !GOOGLE_KEY) return;

    let mounted = true;
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
      // set loader attributes
      if (loaderRef.current) {
        try {
          loaderRef.current.setAttribute('key', GOOGLE_KEY);
          loaderRef.current.setAttribute('solution-channel', 'GMP_GE_placepicker_v2');
        } catch (e) {
          // ignore
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
      }

      // cleanup
      return () => {
        mounted = false;
        if (placePicker) placePicker.removeEventListener('gmpx-placechange', onPlaceChange);
      };
    };

    let cleanupFn: (() => void) | undefined;
    configure().then((c) => { if (typeof c === 'function') cleanupFn = c as any; }).catch(() => {});

    return () => { if (cleanupFn) cleanupFn(); };
  }, [isOpen, GOOGLE_KEY]);

  const doSearch = async (q: string) => {
    if (!q || q.trim().length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const encoded = encodeURIComponent(q.trim());
      const res: any = await apiClient.get(`/maps/search?query=${encoded}`);
      setResults(res || []);
    } catch (err: any) {
      console.error('Search error', err);
      // eslint-disable-next-line no-console
      alert('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDetails = async (place_id: string) => {
    setDetailsLoading(true);
    try {
      const res: any = await apiClient.get(`/maps/details?place_id=${encodeURIComponent(place_id)}`);
      setSelected({
        place_id: res.place_id,
        name: res.name,
        formatted_address: res.formatted_address,
        lat: res.lat,
        lng: res.lng,
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
        formatted_address: selected.formatted_address,
        lat: selected.lat,
        lng: selected.lng,
      };
      await apiClient.post('/maps/connect', payload);
      onConnected(payload);
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
            {/* If Google key present, render the client-side Place Picker UI using the GMPX components */}
            {GOOGLE_KEY ? (
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
                  src={`https://www.openstreetmap.org/export/embed.html?bbox=${selected.lng! - 0.002}%2C${selected.lat! - 0.002}%2C${selected.lng! + 0.002}%2C${selected.lat! + 0.002}&layer=mapnik&marker=${selected.lat}%2C${selected.lng}`}
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
