import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import '../styles/MapAoiPicker.css';

const DEFAULT_BOUNDS = [[-90, -180], [90, 180]];
const PRESET_AOIS = {
  california: { label: 'California', bounds: [[32.5, -125], [42, -114]] },
  'north-india': { label: 'North India', bounds: [[22, 70], [32, 85]] },
  amazon: { label: 'Amazon Basin', bounds: [[-15, -80], [5, -50]] },
  'australia-nsw': { label: 'Australia NSW', bounds: [[-38, 140], [-28, 155]] },
  'east-siberia': { label: 'East Siberia', bounds: [[50, 110], [70, 140]] }
};

export default function MapAoiPicker({ onAoiSelect, selectedAoi }) {
  const mapRef = useRef(null);
  const mapContainer = useRef(null);
  const [drawControl, setDrawControl] = useState(null);
  const [drawnLayer, setDrawnLayer] = useState(null);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = L.map(mapContainer.current, {
      center: [0, 0],
      zoom: 2,
      maxBounds: DEFAULT_BOUNDS,
      maxBoundsViscosity: 1.0
    });
    mapRef.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const dc = new L.Control.Draw({
      position: 'topleft',
      draw: {
        polygon: { allowIntersection: false, showArea: true },
        rectangle: true,
        circle: false,
        marker: false,
        circlemarker: false,
        polyline: false
      },
      edit: { featureGroup: drawnItems, remove: true }
    });
    map.addControl(dc);
    setDrawControl(dc);

    map.on(L.Draw.Event.CREATED, (e) => {
      const layer = e.layer;
      drawnItems.clearLayers();
      drawnItems.addLayer(layer);
      setDrawnLayer(layer);
      const bounds = layer.getBounds();
      const aoiId = boundsToAoiId(bounds);
      if (aoiId) onAoiSelect(aoiId);
    });

    map.on(L.Draw.Event.EDITED, (e) => {
      const layers = e.layers;
      layers.eachLayer((layer) => {
        const bounds = layer.getBounds();
        const aoiId = boundsToAoiId(bounds);
        if (aoiId) onAoiSelect(aoiId);
      });
    });

    map.on(L.Draw.Event.DELETED, () => {
      setDrawnLayer(null);
    });

    if (selectedAoi && PRESET_AOIS[selectedAoi]) {
      const b = PRESET_AOIS[selectedAoi].bounds;
      const rect = L.rectangle(b, { color: '#f0883e', weight: 2, dashArray: '5,5' });
      drawnItems.addLayer(rect);
      setDrawnLayer(rect);
      map.fitBounds(b);
    }

    return () => map.remove();
  }, [onAoiSelect, selectedAoi]);

  const boundsToAoiId = (bounds) => {
    const [[south, west], [north, east]] = [
      [bounds.getSouthWest().lat, bounds.getSouthWest().lng],
      [bounds.getNorthEast().lat, bounds.getNorthEast().lng]
    ];
    for (const [id, meta] of Object.entries(PRESET_AOIS)) {
      const [[ps, pw], [pn, pe]] = meta.bounds;
      if (south >= ps && north <= pn && west >= pw && east <= pe) return id;
    }
    return 'custom';
  };

  return (
    <div className="map-aoi-picker">
      <div className="map-presets">
        {Object.entries(PRESET_AOIS).map(([id, meta]) => (
          <button
            key={id}
            className={`preset-btn ${selectedAoi === id ? 'active' : ''}`}
            onClick={() => {
              const [[south, west], [north, east]] = meta.bounds;
              const rect = L.rectangle([[south, west], [north, east]], { color: '#f0883e', weight: 2, dashArray: '5,5' });
              if (mapRef.current) {
                const drawnItems = mapRef.current._layers[Object.keys(mapRef.current._layers).find(k => mapRef.current._layers[k] instanceof L.FeatureGroup)];
                if (drawnItems) {
                  drawnItems.clearLayers();
                  drawnItems.addLayer(rect);
                }
                mapRef.current.fitBounds(rect.getBounds());
              }
              onAoiSelect(id);
            }}
          >
            {meta.label}
          </button>
        ))}
      </div>
      <div ref={mapContainer} className="map-container" />
      <div className="map-hint">
        Draw a rectangle/polygon or click a preset. Custom areas use the nearest preset's data.
      </div>
    </div>
  );
}