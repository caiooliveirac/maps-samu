import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMapEvents,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { dispatchByCoords, dispatchByAddress, fetchBases } from './services/api';

// ── Map center: Salvador ──
const SALVADOR_CENTER = [-12.9714, -38.5124];
const DEFAULT_ZOOM = 12;

// ── Custom Icons ──
const createIcon = (color, size = 28) =>
  L.divIcon({
    className: '',
    html: `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="${color}" opacity="0.9" stroke="#fff" stroke-width="2"/>
      <text x="12" y="16" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">+</text>
    </svg>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });

const ICONS = {
  base: createIcon('#3b82f6', 24),
  baseTop: createIcon('#22c55e', 32),
  occurrence: L.divIcon({
    className: '',
    html: `<svg width="36" height="36" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="#ef4444" opacity="0.9" stroke="#fff" stroke-width="2">
        <animate attributeName="r" values="8;10;8" dur="1.5s" repeatCount="indefinite"/>
      </circle>
      <text x="12" y="16" text-anchor="middle" fill="#fff" font-size="12" font-weight="bold">!</text>
    </svg>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  }),
};

// ── Time Period Labels ──
const PERIOD_LABELS = {
  NORMAL: '🟢 Trânsito Normal',
  MORNING_RUSH: '🔴 Rush Manhã',
  EVENING_RUSH: '🔴 Rush Noite',
  NIGHT: '🟣 Noturno',
  WEEKEND: '🟡 Fim de Semana',
};

const ROUTING_MODE_META = {
  OSRM: { icon: '🟢', label: 'OSRM' },
  MIXED: { icon: '🟡', label: 'OSRM parcial' },
  FORMULA: { icon: '🔴', label: 'Fallback fórmula' },
};

// ── Map click handler component ──
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// ── Fly to location ──
function FlyTo({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) {
      map.flyTo(position, 14, { duration: 0.8 });
    }
  }, [position, map]);
  return null;
}

// ── Result Card ──
function ResultCard({ base, isTop, onClick }) {
  const rankClass = base.rank <= 3 ? `rank-${base.rank}` : '';

  return (
    <div
      className={`result-card ${rankClass}`}
      onClick={() => onClick(base)}
    >
      <div className="result-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className={`rank-badge ${base.rank > 3 ? 'rank-badge-default' : ''}`}>
            {base.rank}
          </div>
          <div>
            <div className="base-name">{base.base_name}</div>
            <div className="base-neighborhood">{base.neighborhood}</div>
          </div>
        </div>
        <div className="time-estimate">
          {base.estimated_minutes.toFixed(0)}
          <span className="time-unit">min</span>
        </div>
      </div>

      <div className="ambulance-list">
        {base.ambulances.map((amb) => (
          <span key={amb.ambulance_id} className={`ambulance-tag ${amb.status}`}>
            <span className={`status-dot ${amb.status}`} />
            {amb.ambulance_code} ({amb.ambulance_type})
          </span>
        ))}
      </div>

      {!base.has_available && (
        <div style={{ marginTop: 8, fontSize: 11, color: '#ef4444', fontWeight: 600 }}>
          ⚠ SEM AMBULÂNCIA DISPONÍVEL NESTA BASE
        </div>
      )}
    </div>
  );
}

// ── Main App ──
export default function App() {
  const [bases, setBases] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [occurrencePos, setOccurrencePos] = useState(null);
  const [flyTarget, setFlyTarget] = useState(null);
  const [selectedBase, setSelectedBase] = useState(null);
  const [coordMode, setCoordMode] = useState(false);
  const [capturedCoords, setCapturedCoords] = useState([]);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const inputRef = useRef(null);

  // Load bases on mount
  useEffect(() => {
    fetchBases()
      .then(setBases)
      .catch((err) => console.error('Failed to load bases:', err));
  }, []);

  // Dispatch handler
  const handleDispatch = useCallback(
    async (lat, lng, address) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setSelectedBase(null);

      try {
        let data;
        if (lat !== undefined && lng !== undefined) {
          data = await dispatchByCoords(lat, lng);
        } else {
          data = await dispatchByAddress(address);
        }

        setResult(data);
        setOccurrencePos([data.occurrence_lat, data.occurrence_lng]);
        setFlyTarget([data.occurrence_lat, data.occurrence_lng]);
      } catch (err) {
        setError({
          message: err.message || 'Erro desconhecido',
          detail: err.detail,
          code: err.code,
        });
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Map click
  const handleMapClick = useCallback(
    (lat, lng) => {
      if (coordMode) {
        setCapturedCoords((prev) => [
          { lat, lng, label: `Ponto ${prev.length + 1}` },
          ...prev,
        ]);
        return;
      }
      setOccurrencePos([lat, lng]);
      handleDispatch(lat, lng);
    },
    [handleDispatch, coordMode]
  );

  // Copy coordinates to clipboard
  const handleCopyCoord = useCallback((coord, index) => {
    const text = `${coord.lat},${coord.lng}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  }, []);

  // Address search
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchText.trim().length >= 3) {
      handleDispatch(undefined, undefined, searchText.trim());
    }
  };

  // Click on result card → fly to base
  const handleBaseClick = (base) => {
    setSelectedBase(base.base_id);
    setFlyTarget([base.latitude, base.longitude]);
  };

  // Line from occurrence to top base
  const topBase = result?.bases_ranked?.[0];
  const routeLine =
    occurrencePos && topBase
      ? [occurrencePos, [topBase.latitude, topBase.longitude]]
      : null;

  const routingMode = result?.routing_mode || (result?.fallback_used ? 'FORMULA' : 'OSRM');
  const routingMeta = ROUTING_MODE_META[routingMode] || ROUTING_MODE_META.OSRM;

  return (
    <div className="app-layout">
      {/* ── MAP ── */}
      <div className="map-container">
        <MapContainer
          center={SALVADOR_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org">OSM</a> &copy; <a href="https://carto.com">CARTO</a>'
          />

          <MapClickHandler onMapClick={handleMapClick} />
          <FlyTo position={flyTarget} />

          {/* Base markers */}
          {bases.map((base) => (
            <Marker
              key={base.id}
              position={[base.latitude, base.longitude]}
              icon={
                topBase && topBase.base_id === base.id
                  ? ICONS.baseTop
                  : ICONS.base
              }
            >
              <Popup>
                <strong>{base.name}</strong>
                <br />
                {base.neighborhood}
                <br />
                Ambulâncias: {base.ambulances.length}
              </Popup>
            </Marker>
          ))}

          {/* Occurrence marker */}
          {occurrencePos && (
            <Marker position={occurrencePos} icon={ICONS.occurrence}>
              <Popup>
                <strong>Ocorrência</strong>
                <br />
                {occurrencePos[0].toFixed(5)}, {occurrencePos[1].toFixed(5)}
              </Popup>
            </Marker>
          )}

          {/* Route line */}
          {routeLine && (
            <Polyline
              positions={routeLine}
              pathOptions={{
                color: '#22c55e',
                weight: 3,
                dashArray: '8 8',
                opacity: 0.8,
              }}
            />
          )}
        </MapContainer>

        {!result && !loading && !coordMode && (
          <div className="map-click-indicator">
            Clique no mapa para localizar a ocorrência
          </div>
        )}

        {coordMode && (
          <div className="map-click-indicator coord-mode-indicator">
            📌 MODO CAPTURA — Clique no mapa para capturar coordenadas
          </div>
        )}
      </div>

      {/* ── SIDE PANEL ── */}
      <div className="side-panel">
        <div className="panel-header">
          <h1>MAPS-SAMU</h1>
          <div className="subtitle">Despacho de Ambulâncias — Salvador, BA</div>
        </div>

        {/* Coord capture toggle */}
        <div style={{ padding: '0 20px 8px' }}>
          <button
            className={`btn-coord-mode ${coordMode ? 'active' : ''}`}
            onClick={() => {
              setCoordMode((prev) => !prev);
              if (coordMode) setCapturedCoords([]);
            }}
          >
            {coordMode ? '✕ Sair do modo captura' : '📌 Capturar Coordenadas'}
          </button>
        </div>

        {/* Captured coordinates list */}
        {coordMode && (
          <div className="coord-capture-panel">
            {capturedCoords.length === 0 && (
              <div style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', padding: 12 }}>
                Clique no mapa para capturar coordenadas.<br />
                Cada clique adiciona um ponto aqui.
              </div>
            )}
            {capturedCoords.map((coord, i) => (
              <div key={i} className="coord-item">
                <div className="coord-values">
                  <span className="coord-label">Lat:</span> {coord.lat}
                  <br />
                  <span className="coord-label">Lng:</span> {coord.lng}
                </div>
                <button
                  className="btn-copy-coord"
                  onClick={() => handleCopyCoord(coord, i)}
                  title="Copiar coordenadas"
                >
                  {copiedIndex === i ? '✓' : '📋'}
                </button>
              </div>
            ))}
            {capturedCoords.length > 0 && (
              <button
                className="btn-copy-all"
                onClick={() => {
                  const csv = 'Latitude,Longitude\n' +
                    capturedCoords.map((c) => `${c.lat},${c.lng}`).join('\n');
                  navigator.clipboard.writeText(csv);
                  setCopiedIndex(-1);
                  setTimeout(() => setCopiedIndex(null), 2000);
                }}
              >
                {copiedIndex === -1 ? '✓ Copiado!' : '📋 Copiar tudo (CSV)'}
              </button>
            )}
          </div>
        )}

        {/* Search */}
        <div className="search-section">
          <form className="search-box" onSubmit={handleSearchSubmit}>
            <input
              ref={inputRef}
              className="search-input"
              type="text"
              placeholder="Endereço da ocorrência..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <button
              className="btn-search"
              type="submit"
              disabled={loading || searchText.trim().length < 3}
            >
              {loading ? '...' : 'Buscar'}
            </button>
          </form>
          <div className="search-hint">
            <strong>Mais rápido:</strong> clique direto no mapa para despacho instantâneo
          </div>

          {result && (
            <div className="dispatch-status-row">
              <span className={`time-period-badge ${result.time_period}`}>
                <span className="period-dot" />
                {PERIOD_LABELS[result.time_period] || result.time_period}
              </span>
              <span
                className={`routing-badge ${routingMode}`}
                title={`Cálculo: ${routingMeta.label} (OSRM direto: ${result.osrm_refined_count || 0}, cache: ${result.osrm_cache_count || 0}, fallback: ${result.fallback_formula_count || 0})`}
              >
                <span aria-hidden="true">{routingMeta.icon}</span>
                {routingMeta.label}
              </span>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="results-section">
          {/* Loading */}
          {loading && (
            <div className="state-message">
              <div className="spinner" />
              <div className="state-title">Calculando rotas...</div>
              <div className="state-desc">Buscando base mais próxima</div>
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="error-message">
              <p>
                <strong>Erro:</strong> {error.message}
              </p>
              {error.detail && (
                <p style={{ marginTop: 4, fontSize: 12, opacity: 0.8 }}>
                  {error.detail}
                </p>
              )}
            </div>
          )}

          {/* Empty state */}
          {!result && !loading && !error && (
            <div className="state-message">
              <div className="state-icon">🗺️</div>
              <div className="state-title">Pronto para despacho</div>
              <div className="state-desc">
                Clique no mapa ou digite o endereço da ocorrência para ver as
                bases mais próximas ordenadas por tempo de chegada.
              </div>
            </div>
          )}

          {/* Fallback warning */}
          {result?.fallback_used && (
            <div className="fallback-warning">
              ⚠ Estimativa aproximada (zona não encontrada na matriz).
              Tempos podem variar.
            </div>
          )}

          {/* Resolved address */}
          {result?.resolved_address && (
            <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12, lineHeight: 1.4 }}>
              📍 {result.resolved_address}
            </div>
          )}

          {/* Result cards */}
          {result?.bases_ranked?.map((base) => (
            <ResultCard
              key={base.base_id}
              base={base}
              isTop={base.rank === 1}
              onClick={handleBaseClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
