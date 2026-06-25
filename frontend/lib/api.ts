const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  health: () => req<any>("/health"),
  metrics: () => req<any>("/metrics"),
  sources: () => req<any>("/sources"),
  seed: () => req<any>("/demo/seed", { method: "POST" }),
  reset: () => req<any>("/demo/reset", { method: "POST" }),
  runJob: (task: string, params?: any) =>
    req<any>("/run", { method: "POST", body: JSON.stringify({ task, params: params || {} }) }),
  getJob: (jobId: string) => req<any>(`/jobs/${jobId}`),
  reportSummary: () => req<any>("/reports/summary"),
  reportPipeline: () => req<any>("/reports/pipeline"),
  reportAnomalies: () => req<any>("/reports/anomalies"),
  updateAnomaly: (id: number, status: string) =>
    req<any>(`/reports/anomalies/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
  candidates: () => req<any>("/candidates"),
  duplicates: () => req<any>("/candidates/duplicates"),
  mergeCandidates: (primaryId: number, secondaryId: number) =>
    req<any>(`/candidates/merge?primary_id=${primaryId}&secondary_id=${secondaryId}`, { method: "POST" }),
  chat: (message: string, history?: any[]) =>
    req<any>("/agent/chat", { method: "POST", body: JSON.stringify({ message, conversation_history: history || [] }) }),
  exportSheets: (format = "csv") =>
    req<any>("/sheets/export", { method: "POST", body: JSON.stringify({ format }) }),
  gmiSettings: () => req<any>("/settings/gmi"),
  syncDemo: (source: string) => req<any>(`/sync/demo/${source}`, { method: "POST" }),
};
