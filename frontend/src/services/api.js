/**
 * API client para o backend MAPS-SAMU.
 * Timeout agressivo de 8s — se não responder, algo está errado.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

class ApiError extends Error {
  constructor(message, code, detail) {
    super(message);
    this.code = code;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeout);

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = body.detail || body;
      throw new ApiError(
        detail.error || `Erro ${res.status}`,
        detail.code || 'UNKNOWN',
        detail.detail || null
      );
    }

    return res.json();
  } catch (err) {
    clearTimeout(timeout);
    if (err.name === 'AbortError') {
      throw new ApiError(
        'Timeout — servidor não respondeu em 8s',
        'TIMEOUT',
        'Verifique a conexão'
      );
    }
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      'Falha na conexão com o servidor',
      'NETWORK',
      err.message
    );
  }
}

/**
 * Despacho por coordenadas (clique no mapa — caminho mais rápido).
 */
export async function dispatchByCoords(lat, lng) {
  return request('/dispatch', {
    method: 'POST',
    body: JSON.stringify({ latitude: lat, longitude: lng }),
  });
}

/**
 * Despacho por endereço textual (mais lento, depende de geocoding).
 */
export async function dispatchByAddress(address) {
  return request('/dispatch', {
    method: 'POST',
    body: JSON.stringify({ address }),
  });
}

/**
 * Lista todas as bases para mostrar no mapa.
 */
export async function fetchBases() {
  return request('/bases');
}

/**
 * Health check.
 */
export async function healthCheck() {
  return request('/health');
}
