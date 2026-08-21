const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    let message = 'No se pudo completar la solicitud.'
    try {
      const errorBody = await response.json()
      message = errorBody.detail || message
    } catch {
      // Keep the generic message when the response is not JSON.
    }
    throw new Error(Array.isArray(message) ? message[0]?.msg || 'Datos invalidos.' : message)
  }

  return response.json()
}

export function listRequests() {
  return request('/api/requests')
}

export function createRequest(payload) {
  return request('/api/requests', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getRequest(requestId) {
  return request(`/api/requests/${requestId}`)
}

export function getEvidenceUrl(requestId) {
  return `${API_BASE_URL}/api/requests/${requestId}/evidence.pdf`
}
