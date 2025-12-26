// In production (Docker), use relative paths since nginx proxies to backend
// In development, use the full URL or fallback to localhost
const API_BASE = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? "" : "http://localhost:8000");

async function handleResponse<T>(res: Response): Promise<T> {
  // Read the response body once as text
  const text = await res.text();
  
  if (!res.ok) {
    let errorMessage = `Request failed: ${res.status}`;
    // Try to parse as JSON for structured error messages
    if (text) {
      try {
        const errorData = JSON.parse(text);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // If not JSON, use the text as error message
        errorMessage = text || errorMessage;
      }
    }
    throw new Error(errorMessage);
  }
  
  // Handle empty responses (e.g., DELETE with no body)
  if (!text) {
    return {} as T;
  }
  
  // Try to parse as JSON, fallback to text
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as T;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  return handleResponse<T>(res);
}

export async function apiPost<TReq, TRes>(
  path: string,
  body: TReq,
  method: string = "POST"
): Promise<TRes> {
  const options: RequestInit = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  // Only include body for non-GET/DELETE requests
  if (method !== "GET" && method !== "DELETE") {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_BASE}${path}`, options);
  return handleResponse<TRes>(res);
}


