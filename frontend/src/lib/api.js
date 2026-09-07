const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function api(path, options = {}) {
  const { token, body, headers, ...requestOptions } = options;
  const isFormData = body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...requestOptions,
    headers: {
      ...(isFormData
        ? {}
        : body !== undefined
          ? { "Content-Type": "application/json" }
          : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined || isFormData ? body : JSON.stringify(body),
  });

  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail = payload?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : payload?.message || `Request failed (${response.status})`;
    throw new ApiError(message, response.status, detail);
  }

  return payload?.data;
}

export function apiRequest(path, options = {}) {
  const token =
    localStorage.getItem("api-anomaly-token") ||
    sessionStorage.getItem("api-anomaly-token");
  return api(path, { ...options, token: options.token || token });
}

export { API_URL };
