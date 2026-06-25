"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertTriangle, CheckCircle, XCircle, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";

function SeverityBadge({ s }: { s: string }) {
  if (s === "high") return <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-700 uppercase tracking-wide">HIGH</span>;
  if (s === "medium") return <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded bg-orange-100 text-orange-700 uppercase tracking-wide">MEDIUM</span>;
  return <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 uppercase tracking-wide">LOW</span>;
}

function CategoryBadge({ c }: { c: string }) {
  const label = c.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  return <span className="text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded">{label}</span>;
}

const PAGE_SIZE = 8;

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [duplicates, setDuplicates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [updating, setUpdating] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([api.reportAnomalies(), api.duplicates()])
      .then(([a, d]) => { setAnomalies(a.anomalies || []); setDuplicates(d.suggestions || []); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function updateStatus(id: number, status: string) {
    setUpdating(id);
    try {
      await api.updateAnomaly(id, status);
      setAnomalies(prev => prev.map(a => a.id === id ? { ...a, status } : a));
    } catch {}
    setUpdating(null);
  }

  async function mergeCandidate(primaryId: number, secondaryId: number) {
    try {
      await api.mergeCandidates(primaryId, secondaryId);
      setDuplicates(prev => prev.filter(d => !(d.candidate_a.id === primaryId && d.candidate_b.id === secondaryId)));
    } catch {}
  }

  const highCount = anomalies.filter(a => a.severity === "high").length;
  const paged = anomalies.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const totalPages = Math.ceil(anomalies.length / PAGE_SIZE);

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Anomalies & Reconciliation</h1>
          <p className="text-sm text-slate-500 mt-0.5">Review and resolve data inconsistencies across your recruiting pipelines.</p>
        </div>
        {highCount > 0 && (
          <span className="flex items-center gap-1.5 text-sm font-semibold text-red-600 bg-red-50 border border-red-200 px-3 py-1.5 rounded-lg">
            <AlertTriangle className="w-4 h-4" /> {highCount} High Priority
          </span>
        )}
      </div>

      <Tabs defaultValue="anomalies">
        <TabsList className="bg-white border border-slate-200 p-1 rounded-lg">
          <TabsTrigger value="anomalies" className="text-sm">Pipeline Anomalies</TabsTrigger>
          <TabsTrigger value="reconciliation" className="text-sm">
            Candidate Reconciliation
            {duplicates.length > 0 && <span className="ml-1.5 text-[10px] bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded-full">{duplicates.length}</span>}
          </TabsTrigger>
        </TabsList>

        {/* Anomalies tab */}
        <TabsContent value="anomalies" className="mt-4">
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/50 text-xs text-slate-500 font-medium">
                  <th className="text-left px-5 py-3">Severity</th>
                  <th className="text-left px-3 py-3">Category</th>
                  <th className="text-left px-3 py-3">Problem Description</th>
                  <th className="text-left px-3 py-3">Recommended Fix</th>
                  <th className="text-left px-3 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400 text-sm">
                    <RefreshCw className="w-4 h-4 animate-spin inline mr-2" />Loading anomalies…
                  </td></tr>
                ) : paged.length === 0 ? (
                  <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400 text-sm">
                    No open anomalies. Run a pipeline refresh to scan for issues.
                  </td></tr>
                ) : paged.map((a: any) => (
                  <tr key={a.id} className={`border-b border-slate-100 hover:bg-slate-50/50 ${a.status !== "open" ? "opacity-50" : ""}`}>
                    <td className="px-5 py-4"><SeverityBadge s={a.severity} /></td>
                    <td className="px-3 py-4"><CategoryBadge c={a.category} /></td>
                    <td className="px-3 py-4">
                      <div className="font-medium text-slate-800 text-xs">{a.title}</div>
                      <div className="text-slate-500 text-[11px] mt-0.5 max-w-xs leading-relaxed">{a.explanation}</div>
                    </td>
                    <td className="px-3 py-4 text-[11px] text-slate-600 max-w-[200px] leading-relaxed">{a.recommended_fix}</td>
                    <td className="px-3 py-4">
                      {a.status === "open" ? (
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => updateStatus(a.id, "resolved")}
                            disabled={updating === a.id}
                            className="flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded hover:bg-emerald-100 transition-colors"
                          >
                            <CheckCircle className="w-3 h-3" />Fix
                          </button>
                          <button
                            onClick={() => updateStatus(a.id, "ignored")}
                            disabled={updating === a.id}
                            className="flex items-center gap-1 text-[11px] text-slate-500 bg-slate-50 border border-slate-200 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
                          >
                            <XCircle className="w-3 h-3" />Ignore
                          </button>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-400 capitalize">{a.status}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 text-xs text-slate-500">
                <span>Showing {(page-1)*PAGE_SIZE+1}–{Math.min(page*PAGE_SIZE, anomalies.length)} of {anomalies.length} anomalies</span>
                <div className="flex items-center gap-2">
                  <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="p-1 rounded hover:bg-slate-100 disabled:opacity-40">
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  {Array.from({length: totalPages}, (_,i) => i+1).map(n => (
                    <button key={n} onClick={() => setPage(n)} className={`w-7 h-7 rounded text-xs ${page===n ? "bg-blue-600 text-white" : "hover:bg-slate-100"}`}>{n}</button>
                  ))}
                  <button onClick={() => setPage(p => Math.min(totalPages,p+1))} disabled={page===totalPages} className="p-1 rounded hover:bg-slate-100 disabled:opacity-40">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Candidate Reconciliation tab */}
        <TabsContent value="reconciliation" className="mt-4">
          <div className="space-y-3">
            {duplicates.length === 0 ? (
              <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-400 text-sm">
                No duplicate candidates detected. Run a full pipeline refresh to scan for duplicates.
              </div>
            ) : duplicates.map((dup: any, i: number) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 p-5">
                <div className="flex items-start gap-4">
                  {/* Candidate A */}
                  <div className="flex-1 bg-slate-50 rounded-lg p-3">
                    <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wide mb-1.5">Candidate A</div>
                    <div className="font-semibold text-slate-800 text-sm">{dup.candidate_a.full_name}</div>
                    <div className="text-xs text-slate-500 mt-1 space-y-0.5">
                      <div>{dup.candidate_a.email_masked}</div>
                      <div>{dup.candidate_a.phone_masked}</div>
                      <div>{dup.candidate_a.location}</div>
                      <div className="text-slate-400">{dup.candidate_a.current_title}</div>
                    </div>
                  </div>

                  {/* Middle info */}
                  <div className="flex flex-col items-center gap-2 pt-4">
                    <div className="text-lg font-bold text-slate-300">≈</div>
                    <div className="text-center">
                      <div className="text-xs font-semibold text-slate-700">{Math.round(dup.confidence * 100)}%</div>
                      <div className="text-[10px] text-slate-400">confidence</div>
                    </div>
                  </div>

                  {/* Candidate B */}
                  <div className="flex-1 bg-slate-50 rounded-lg p-3">
                    <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wide mb-1.5">Candidate B</div>
                    <div className="font-semibold text-slate-800 text-sm">{dup.candidate_b.full_name}</div>
                    <div className="text-xs text-slate-500 mt-1 space-y-0.5">
                      <div>{dup.candidate_b.email_masked}</div>
                      <div>{dup.candidate_b.phone_masked}</div>
                      <div>{dup.candidate_b.location}</div>
                      <div className="text-slate-400">{dup.candidate_b.current_title}</div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 pt-3">
                    <div className="text-[11px] text-slate-500 max-w-[140px] leading-relaxed">{dup.reason}</div>
                    <button
                      onClick={() => mergeCandidate(dup.candidate_a.id, dup.candidate_b.id)}
                      className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md transition-colors"
                    >
                      Approve Merge
                    </button>
                    <button
                      onClick={() => setDuplicates(prev => prev.filter((_,j) => j !== i))}
                      className="text-xs text-slate-500 border border-slate-200 px-3 py-1.5 rounded-md hover:bg-slate-50"
                    >
                      Ignore
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
