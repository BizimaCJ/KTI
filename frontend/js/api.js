// All network calls live here so the rest of the app never touches fetch().
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function getJson(path, { signal } = {}) {
  let response;
  try {
    response = await fetch(path, { signal, headers: { Accept: 'application/json' } });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0);
  }
  if (!response.ok) {
    let detail = 'Something went wrong. Please try again.';
    try {
      const body = await response.json();
      if (body && typeof body.detail === 'string') detail = body.detail;
    } catch (_) { /* keep the default message */ }
    throw new ApiError(detail, response.status);
  }
  return response.json();
}

export const getOverview = (options) => getJson('/api/overview', options);
