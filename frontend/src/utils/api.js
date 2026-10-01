/**
 * Backend client.
 *
 * The API base is resolved from VITE_API_BASE when set, otherwise from
 * Vite's dev-server proxy (see vite.config.js) so the browser only ever talks
 * to one origin and no CORS preflight is needed during development.
 */

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* response had no JSON body */
    }
    throw new Error(detail);
  }

  return response.json();
}

/** Which providers are live, so the UI can be honest about the mode. */
export function getHealth() {
  return request("/health");
}

/** Queue a generation; resolves as soon as the job is accepted. */
export function createGeneration({ topic, num_slides, language, tone }) {
  return request("/api/generate", {
    method: "POST",
    body: JSON.stringify({ topic, num_slides, language, tone }),
  });
}

/** Poll a finished job for its payload. */
export function getJob(jobId) {
  return request(`/api/job/${jobId}`);
}

export function videoUrl(filename) {
  return `${BASE}/api/video/${encodeURIComponent(filename)}`;
}