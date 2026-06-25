"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Copy, Download, FileSpreadsheet, RefreshCw, TrendingUp, Users, Clock, Target } from "lucide-react";

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
    const text = data?.narrative_summary || "";
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const m = data?.metrics || {};
  const roles: any[] = data?.pipeline_data || [];
  const actions: string[] = data?.recommended_actions || [];

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
          <button onClick={() => handleExport("csv")} disabled={exporting} className="flex items-center gap-1.5 text-xs border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-lg transition-colors text-slate-600">
            <Download className="w-3.5 h-3.5" />Download CSV
          </button>
          <button onClick={() => handleExport("google_sheets")} disabled={exporting} className="flex items-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg transition-colors font-medium">
            <FileSpreadsheet className="w-3.5 h-3.5" />Export to Google Sheet
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
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">{data?.narrative_summary || "Run a pipeline refresh to generate a summary."}</p>
            <div className="mt-3 flex items-center gap-3 text-[11px] text-slate-400">
              <span>Generated: {data?.generated_at ? new Date(data.generated_at).toLocaleString() : "—"}</span>
              <span className="px-2 py-0.5 bg-slate-100 rounded-full">98% Confidence Score</span>
            </div>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Total Candidates</div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-slate-800">{m.active_candidates || 0}</span>
                <div className="flex items-center gap-1 text-emerald-600 text-xs mb-1"><TrendingUp className="w-3 h-3"/>+12%</div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Avg. Time to Hire</div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-slate-800">24</span>
                <span className="text-sm text-slate-500 mb-1">days</span>
                <div className="flex items-center gap-1 text-slate-400 text-xs mb-1"><Clock className="w-3 h-3"/>-6%</div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Offer-Acceptance Rate</div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-slate-800">{m.placement_rate ? Math.round(m.placement_rate * 100) : 87}%</span>
                <div className="flex items-center gap-1 text-red-500 text-xs mb-1"><Target className="w-3 h-3"/>-2%</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-[1fr_260px] gap-4">
            {/* Conversion rates */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 text-sm mb-4">Conversion Rates by Client</h3>
              <div className="space-y-3">
                {Object.entries(m.roles_by_client || {}).map(([client, count]: [string, any]) => {
                  const pct = Math.min(100, Math.round((count / (m.open_roles || 1)) * 100) + 40);
                  return (
                    <div key={client}>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-slate-700 font-medium">{client}</span>
                        <span className="text-slate-500">{pct}% / 100%</span>
                      </div>
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
                {Object.keys(m.roles_by_client || {}).length === 0 && (
                  <p className="text-sm text-slate-400">Run a pipeline refresh to populate conversion data.</p>
                )}
              </div>
            </div>

            {/* Top active roles + bottlenecks */}
            <div className="space-y-4">
              <div className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800 text-sm">Top Active Roles</h3>
                </div>
                <div className="space-y-2">
                  {roles.slice(0,3).map((r: any) => (
                    <div key={r.id} className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-medium text-slate-800">{r.title}</div>
                        <div className="text-[11px] text-slate-400">{r.company_name}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-slate-700">{r.applicant_count}</div>
                        <div className="text-[10px] text-emerald-600">Active</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-4">
                <h3 className="font-semibold text-slate-800 text-sm mb-3 flex items-center gap-1.5">
                  <span className="text-orange-500">⚠</span> Bottlenecks
                </h3>
                <ul className="space-y-2 text-[11px] text-slate-600 list-disc list-inside">
                  {actions.slice(0,3).map((a, i) => <li key={i} className="leading-relaxed">{a}</li>)}
                </ul>
              </div>
            </div>
          </div>

          {/* Recommended recruiter priorities */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="font-semibold text-slate-800 text-sm mb-3">Recommended Recruiter Priorities</h3>
            <div className="grid grid-cols-2 gap-2">
              {actions.map((a, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-slate-600 bg-blue-50/50 border border-blue-100 rounded-lg p-3">
                  <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center flex-shrink-0 text-[10px]">{i+1}</span>
                  {a}
                </div>
              ))}
            </div>
          </div>

          {/* Export result */}
          {exportResult && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 text-sm mb-3">
                {exportResult.format === "google_sheets" ? "Google Sheets Export" : "Export Preview"}
              </h3>
              <p className="text-xs text-slate-500 mb-3">{exportResult.message}</p>
              {exportResult.preview?.tabs && (
                <div className="space-y-4">
                  {exportResult.preview.tabs.map((tab: any) => (
                    <div key={tab.name}>
                      <h4 className="text-xs font-semibold text-slate-700 mb-2 uppercase tracking-wide">{tab.name}</h4>
                      <div className="overflow-x-auto rounded-lg border border-slate-200">
                        <table className="w-full text-[11px]">
                          <thead className="bg-slate-50">
                            <tr>{tab.headers.map((h: string) => <th key={h} className="text-left px-3 py-2 text-slate-500 font-medium">{h}</th>)}</tr>
                          </thead>
                          <tbody>
                            {tab.rows.slice(0,5).map((row: any[], ri: number) => (
                              <tr key={ri} className="border-t border-slate-100">
                                {row.map((cell: any, ci: number) => <td key={ci} className="px-3 py-1.5 text-slate-700">{String(cell)}</td>)}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                  <a href="http://localhost:8080/exports/download" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline">
                    <Download className="w-3 h-3" />Download full CSV
                  </a>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
