const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, code, status) {
    super(message)
    this.name = 'ApiError'
    this.code = code || 'API_ERROR'
    this.status = status || 500
  }
}

async function parseResponse(response) {
  let payload = {}
  try {
    payload = await response.json()
  } catch {
    payload = {}
  }

  if (!response.ok) {
    throw new ApiError(
      payload.message || 'Something went wrong. Please try again.',
      payload.error || 'REQUEST_FAILED',
      response.status,
    )
  }
  return payload
}

/**
 * Fetch slot capacities for a date (public endpoint; returns aggregate counts only, zero PII).
 */
export async function fetchSlots(dateStr = '') {
  const qs = dateStr ? `?date=${encodeURIComponent(dateStr)}` : ''
  const response = await fetch(`${API_BASE}/slots${qs}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  })
  return parseResponse(response)
}

/**
 * Submit a new household 5-gallon water refill order.
 */
export async function submitOrder(orderPayload) {
  const response = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(orderPayload),
  })
  return parseResponse(response)
}
