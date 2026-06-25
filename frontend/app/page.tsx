"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Briefcase, Users, Send, MessageSquare, Gift, MapPin,
  AlertTriangle, Clock, TrendingUp, TrendingDown, RefreshCw
} from "lucide-react";

function SeverityBadge({ severity }: { severity: string }) {
  if (severity === "high") return <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-100 text-red-700 uppercase tracking-wide">HIGH</span>;
  if (severity === "medium") return <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 uppercase tracking-wide">MED</span>;
  return <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 uppercase tracking-wide">LOW</span>;
}

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const summary = await api.reportSummary();
      setData(summary);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener("pipeline-refreshed", handler);
    return () => window.removeEventListener("pipeline-refreshed", handler);
  }, [load]);

  const m = data?.metrics || {};
  const roles: any[] = data?.pipeline_data || [];
  const anomalies: any[] = data?.top_anomalies || [];

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-slate-400 gap-2">
      <RefreshCw className="w-4 h-4 animate-spin" /> Loading pipeline data…
    </div>
  );

  return (
    <div className="space-y-5 max-w-[1400px]">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Overview</h1>
          <p className="text-sm text-slate-500 mt-0.5">Real-time recruiting pipeline metrics and anomalies.</p>
        </div>
        <div className="flex gap-2">
          {["All Sources","All Clients","All Recruiters"].map(f => (
            <select key={f} className="text-xs border border-slate-200 rounded-md px-2.5 py-1.5 bg-white text-slate-600"><option>{f}</option></select>
          ))}
        </div>
      </div>

      {/* Top 4 */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label:"Open Roles", value: m.open_roles??0, icon: Briefcase, color:"blue" },
          { label:"Active Candidates", value: m.active_candidates??0, icon: Users, color:"purple" },
          { label:"Interviews", value: m.interview_count??0, icon: MessageSquare, color:"green" },
          { label:"Placements", value: m.placement_count??0, icon: Gift, color:"orange" },
        ].map(c => (
          <div key={c.label} className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">{c.label}</span>
            </div>
            <div className="text-2xl font-bold text-slate-800">{c.value}</div>
          </div>
        ))}
      </div>

      {/* Second row */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Submitted</div>
          <div className="flex items-center gap-2"><Send className="w-4 h-4 text-blue-400" /><span className="text-xl font-bold text-slate-800">{m.submitted_to_client_count??0}</span></div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Offers</div>
          <div className="flex items-center gap-2"><Gift className="w-4 h-4 text-emerald-400" /><span className="text-xl font-bold text-slate-800">{m.offer_count??0}</span></div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Stale Roles</div>
          <div className="flex items-center gap-2"><Clock className="w-4 h-4 text-orange-400" /><span className="text-xl font-bold text-slate-800">{m.stale_role_count??0}</span></div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4 border-l-4 border-l-red-400">
          <div className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Anomalies</div>
          <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-red-400" /><span className="text-xl font-bold text-slate-800">{m.anomaly_count??0}</span></div>
        </div>
      </div>

      {/* Pipeline table + anomalies */}
      <div className="grid grid-cols-[1fr_310px] gap-4">
        <div className="bg-white rounded-xl border border-slate-200">
          <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
            <h2 className="font-semibold text-slate-800 text-sm">Pipeline Overview</h2>
            <a href="/reports" className="text-xs text-blue-600 hover:underline">View All →</a>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500">
                  <th className="text-left px-5 py-2.5 font-medium">Role & Client</th>
                  <th className="text-left px-3 py-2.5 font-medium">Location</th>
                  <th className="text-left px-3 py-2.5 font-medium">Pay Range</th>
                  <th className="text-right px-3 py-2.5 font-medium">App</th>
                  <th className="text-left px-3 py-2.5 font-medium">Funnel</th>
                </tr>
              </thead>
              <tbody>
                {roles.slice(0,6).map((role:any) => {
                  const loc = role.remote_type==="remote" ? "Remote" : [role.location_city,role.location_state].filter(Boolean).join(", ");
                  const pay = role.pay_display || (role.pay_max ? `$${role.pay_max}` : null);
                  return (
                    <tr key={role.id} className="border-b border-slate-50 hover:bg-slate-50/50">
                      <td className="px-5 py-3">
                        <div className="font-medium text-slate-800">{role.title}</div>
                        <div className="text-slate-400 text-[11px]">{role.company_name}</div>
                      </td>
                      <td className="px-3 py-3 text-slate-600"><MapPin className="w-3 h-3 inline mr-1 text-slate-400"/>{loc||"—"}</td>
                      <td className="px-3 py-3">
                        {pay ? <span className="text-slate-600">{pay}</span> : <span className="text-orange-500 font-medium">Missing Data</span>}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold text-slate-700">{role.applicant_count}</td>
                      <td className="px-3 py-3">
                        <div className="flex gap-1 items-center text-[10px] text-slate-400">
                          {[
                            {v:role.submitted_count,label:"Sub",color:"bg-blue-400"},
                            {v:role.interview_count,label:"Int",color:"bg-emerald-400"},
                            {v:role.offer_count,label:"Off",color:"bg-orange-400"},
                          ].map(b => (
                            <div key={b.label} className="flex flex-col items-center gap-0.5">
                              <div className="w-12 h-1.5 bg-slate-100 rounded-full">
                                <div className={`h-full ${b.color} rounded-full`} style={{width:`${role.applicant_count>0?Math.round(b.v/role.applicant_count*100):0}%`}}/>
                              </div>
                              <span>{b.label}</span>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Anomalies panel */}
        <div className="bg-white rounded-xl border border-slate-200">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h2 className="font-semibold text-slate-800 text-sm">Recent Anomalies</h2>
            <span className="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-semibold">
              {anomalies.filter((a:any)=>a.severity==="high").length} Active
            </span>
          </div>
          <div className="p-3 space-y-2">
            {anomalies.slice(0,5).map((a:any) => (
              <div key={a.id} className="p-3 rounded-lg border border-slate-100 hover:border-slate-200">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <SeverityBadge severity={a.severity}/>
                  <span className="text-[10px] text-slate-400 capitalize">{a.severity} severity</span>
                </div>
                <p className="text-xs font-medium text-slate-700 leading-snug">{a.title}</p>
                <p className="text-[11px] text-slate-500 mt-1 leading-relaxed line-clamp-2">{a.explanation}</p>
                <a href="/anomalies" className="text-[11px] text-blue-600 hover:underline mt-1.5 block">Review Details</a>
              </div>
            ))}
            {anomalies.length===0 && <p className="text-xs text-slate-400 text-center py-6">Run a pipeline refresh to detect anomalies.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
