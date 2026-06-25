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
  candidates: (params?: { limit?: number; stage?: string }) => {
    const qs = params ? "?" + new URLSearchParams(Object.entries(params).filter(([, v]) => v != null) as string[][]).toString() : "";
    return req<any>(`/candidates${qs}`);
  },
  candidate: (id: number) => req<any>(`/candidates/${id}`),
  duplicates: () => req<any>("/candidates/duplicates"),
  mergeCandidates: (primaryId: number, secondaryId: number) =>
    req<any>(`/candidates/merge?primary_id=${primaryId}&secondary_id=${secondaryId}`, { method: "POST" }),
  roles: () => req<any>("/roles"),
  roleCandidates: (roleId: number) => req<any>(`/roles/${roleId}/candidates`),
  chat: (message: string, history?: any[]) =>
    req<any>("/agent/chat", { method: "POST", body: JSON.stringify({ message, conversation_history: history || [] }) }),
  exportSheets: (format = "csv") =>
    req<any>("/sheets/export", { method: "POST", body: JSON.stringify({ format }) }),
  gmiSettings: () => req<any>("/settings/gmi"),
  connectorSettings: () => req<any>("/settings/connectors"),
  connectors: () => req<any>("/connectors"),
  connectorFields: (source: string) => req<any>(`/connectors/${source}/fields`),
  connectorStatus: (source: string) => req<any>(`/connectors/${source}/status`),
  saveCredentials: (source: string, creds: Record<string, string>) =>
    req<any>(`/connectors/${source}/credentials`, { method: "POST", body: JSON.stringify(creds) }),
  deleteCredentials: (source: string) =>
    req<any>(`/connectors/${source}/credentials`, { method: "DELETE" }),
  googleOAuthUrl: () => req<any>("/connectors/google_sheets/oauth/url"),
  syncConnector: (source: string) =>
    req<any>(`/connectors/${source}/sync`, { method: "POST" }),
  onboardingStatus: () => req<any>("/onboarding/status"),
  draftAction: (body: { action_type: string; candidate_id?: number; context?: any }) =>
    req<any>("/actions/draft", { method: "POST", body: JSON.stringify(body) }),
  uploadFile: async (file: File, confirmImport = false): Promise<any> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/sync/file?confirm_import=${confirmImport}`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(`Upload error ${res.status}`);
    return res.json();
  },
};
