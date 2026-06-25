"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Copy, Download, FileSpreadsheet, RefreshCw, TrendingUp, AlertTriangle } from "lucide-react";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">{label}</div>
      <div className="text-3xl font-bold text-slate-800">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  );
}

export default function ReportsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.reportSummary().then(setData).catch(console.error).finally(() => setLoading(false));
    const h = () => api.reportSummary().then(setData).catch(console.error);
    window.addEventListener("pipeline-refreshed", h);
    return () => window.removeEventListener("pipeline-refreshed", h);
  }, []);

  async function handleExport(format: string) {
    setExporting(true);
    try {
      const result = await api.exportSheets(format);
      setExportResult(result);
    } catch {}
    setExporting(false);
  }

  function copyText() {
    navigator.clipboard.writeText(data?.narrative_summary || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const m = data?.metrics || {};
  const roles: any[] = data?.pipeline_data || [];
  const actions: string[] = data?.recommended_actions || [];
  const anomalies: any[] = data?.top_anomalies || [];

  // Derived real rates from actual metrics (no fabricated numbers)
  const submitRate = m.submitted_to_client_count && m.active_candidates
    ? Math.round((m.submitted_to_client_count / m.active_candidates) * 100)
    : null;
  const interviewRate = m.interview_count && m.submitted_to_client_count
    ? Math.round((m.interview_count / m.submitted_to_client_count) * 100)
    : null;
  const offerRate = m.offer_count && m.interview_count
    ? Math.round((m.offer_count / m.interview_count) * 100)
    : null;
  const placeRate = m.placement_count && m.offer_count
    ? Math.round((m.placement_count / m.offer_count) * 100)
    : null;

  return (
    <div className="space-y-5 max-w-4xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Executive Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manager-ready summary of pipeline performance.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={copyText} className="flex items-center gap-1.5 text-xs border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-lg transition-colors text-slate-600">
            <Copy className="w-3.5 h-3.5" />{copied ? "Copied!" : "Copy Summary"}
          </button>
          <a
            href="http://localhost:8080/exports/download"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-lg transition-colors text-slate-600"
          >
            <Download className="w-3.5 h-3.5" />Download CSV
          </a>
          <button
            onClick={() => handleExport("google_sheets")}
            disabled={exporting}
            className="flex items-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg transition-colors font-medium disabled:opacity-60"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            {exporting ? "Exporting…" : "Export to Google Sheets"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-slate-400 py-8"><RefreshCw className="w-4 h-4 animate-spin" />Loading report…</div>
      ) : (
        <>
          {/* AI Executive Summary */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-5 h-5 bg-blue-600 rounded flex items-center justify-center">
                <TrendingUp className="w-3 h-3 text-white" />
              </div>
              <h2 className="font-semibold text-slate-800">AI Executive Summary</h2>
              <span className="ml-auto text-[10px] text-slate-400">
                Generated {data?.generated_at ? new Date(data.generated_at).toLocaleString() : "—"}
              </span>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">
              {data?.narrative_summary || "Run a pipeline refresh to generate a summary."}
            </p>
          </div>

          {/* Pipeline funnel — real numbers only */}
          <div className="grid grid-cols-4 gap-3">
            <StatCard label="Active Candidates" value={m.active_candidates ?? "—"} />
            <StatCard label="Submitted to Client" value={m.submitted_to_client_count ?? "—"}
              sub={submitRate != null ? `${submitRate}% of active` : undefined} />
            <StatCard label="In Interview" value={m.interview_count ?? "—"}
              sub={interviewRate != null ? `${interviewRate}% of submitted` : undefined} />
            <StatCard label="Placements" value={m.placement_count ?? "—"}
              sub={placeRate != null ? `${placeRate}% offer → placed` : undefined} />
          </div>

          {/* Funnel conversion */}
          <div className="grid grid-cols-[1fr_260px] gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 text-sm mb-4">Funnel Conversion</h3>
              {[
                { label: "Applied → Submitted", value: submitRate },
                { label: "Submitted → Interview", value: interviewRate },
                { label: "Interview → Offer", value: offerRate },
                { label: "Offer → Placed", value: placeRate },
              ].map(({ label, value }) => (
                <div key={label} className="mb-3">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-slate-700 font-medium">{label}</span>
                    <span className="text-slate-500">{value != null ? `${value}%` : "—"}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: value != null ? `${Math.min(value, 100)}%` : "0%" }}
                    />
                  </div>
                </div>
              ))}
              {submitRate == null && (
                <p className="text-xs text-slate-400 mt-2">Run a pipeline refresh to populate conversion rates.</p>
              )}
            </div>

            {/* Right column */}
            <div className="space-y-4">
              <div className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800 text-sm">Top Active Roles</h3>
                </div>
                <div className="space-y-2">
                  {roles.slice(0, 3).map((r: any) => (
                    <div key={r.id} className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-medium text-slate-800">{r.title}</div>
                        <div className="text-[11px] text-slate-400">{r.company_name}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-slate-700">{r.applicant_count}</div>
                        <div className="text-[10px] text-emerald-600">{r.openings_count} open</div>
                      </div>
                    </div>
                  ))}
                  {roles.length === 0 && <p className="text-xs text-slate-400">No roles found.</p>}
                </div>
              </div>

              {anomalies.filter((a: any) => a.severity === "high").length > 0 && (
                <div className="bg-red-50 rounded-xl border border-red-200 p-4">
                  <h3 className="font-semibold text-red-800 text-sm mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    High-Priority Issues
                  </h3>
                  <ul className="space-y-1.5">
                    {anomalies.filter((a: any) => a.severity === "high").slice(0, 3).map((a: any) => (
                      <li key={a.id} className="text-[11px] text-red-700 leading-relaxed">• {a.title}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Recommended recruiter priorities */}
          {actions.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 text-sm mb-3">Recommended Recruiter Priorities</h3>
              <div className="grid grid-cols-2 gap-2">
                {actions.map((a, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-600 bg-blue-50/50 border border-blue-100 rounded-lg p-3">
                    <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">{i + 1}</span>
                    {a}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Roles by client */}
          {Object.keys(m.roles_by_client || {}).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 text-sm mb-4">Open Roles by Client</h3>
              <div className="space-y-3">
                {Object.entries(m.roles_by_client as Record<string, number>)
                  .sort(([, a], [, b]) => b - a)
                  .map(([client, count]) => {
                    const max = Math.max(...Object.values(m.roles_by_client as Record<string, number>));
                    const pct = Math.round((count / max) * 100);
                    return (
                      <div key={client}>
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-slate-700 font-medium">{client}</span>
                          <span className="text-slate-500">{count} role{count !== 1 ? "s" : ""}</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Export result */}
          {exportResult && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 text-sm mb-2">
                {exportResult.format === "google_sheets" ? "Google Sheets Export" : "Export"}
              </h3>
              <p className="text-xs text-slate-600 mb-2">{exportResult.message}</p>
              {exportResult.sheet_url && (
                <a href={exportResult.sheet_url} target="_blank" rel="noreferrer"
                  className="text-xs text-blue-600 underline">{exportResult.sheet_url}</a>
              )}
              {!exportResult.success && exportResult.status === "needs_credentials" && (
                <p className="text-xs text-amber-700 mt-1">
                  Set <code className="bg-amber-50 px-1 rounded">GOOGLE_SHEETS_CREDENTIALS_JSON</code> and{" "}
                  <code className="bg-amber-50 px-1 rounded">GOOGLE_SHEETS_SPREADSHEET_ID</code> in .env to enable.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
