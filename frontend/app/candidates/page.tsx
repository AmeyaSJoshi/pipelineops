"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Users, MapPin, Briefcase, RefreshCw, Search } from "lucide-react";

const STAGE_COLORS: Record<string, string> = {
  new_lead: "bg-slate-100 text-slate-600",
  applied: "bg-blue-50 text-blue-700",
  recruiter_screen: "bg-cyan-50 text-cyan-700",
  qualified: "bg-teal-50 text-teal-700",
  submitted_to_client: "bg-indigo-50 text-indigo-700",
  client_review: "bg-violet-50 text-violet-700",
  interview_scheduled: "bg-purple-50 text-purple-700",
  interview_completed: "bg-fuchsia-50 text-fuchsia-700",
  offer: "bg-orange-50 text-orange-700",
  placed: "bg-emerald-100 text-emerald-700",
  rejected: "bg-red-50 text-red-500",
  withdrawn: "bg-slate-100 text-slate-400",
};

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.candidates().then(d => setCandidates(d.candidates || [])).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = candidates.filter(c =>
    !search || c.full_name.toLowerCase().includes(search.toLowerCase()) ||
    c.location?.toLowerCase().includes(search.toLowerCase()) ||
    c.current_title?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-5 max-w-4xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Candidates</h1>
          <p className="text-sm text-slate-500 mt-0.5">All active candidates across your recruiting pipeline.</p>
        </div>
        <a href="/anomalies" className="text-xs text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-100 transition-colors">
          View Duplicate Suggestions →
        </a>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-2 max-w-xs">
        <Search className="w-3.5 h-3.5 text-slate-400" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search candidates…"
          className="text-xs text-slate-700 placeholder:text-slate-400 outline-none flex-1 bg-transparent"
        />
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-slate-400 py-8"><RefreshCw className="w-4 h-4 animate-spin"/>Loading candidates…</div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50/70 border-b border-slate-100 text-xs text-slate-500 font-medium">
                <th className="text-left px-5 py-3">Name</th>
                <th className="text-left px-3 py-3">Contact</th>
                <th className="text-left px-3 py-3">Location</th>
                <th className="text-left px-3 py-3">Current Role</th>
                <th className="text-left px-3 py-3">Stage</th>
              <th className="text-right px-5 py-3">Applications</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c: any) => (
                <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-xs font-semibold text-slate-600">
                        {c.full_name.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium text-slate-800">{c.full_name}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-xs text-slate-500 space-y-0.5">
                    {c.email_masked && <div>{c.email_masked}</div>}
                    {c.phone_masked && <div>{c.phone_masked}</div>}
                  </td>
                  <td className="px-3 py-3">
                    {c.location && (
                      <div className="flex items-center gap-1 text-xs text-slate-600">
                        <MapPin className="w-3 h-3 text-slate-400"/>{c.location}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {c.current_title && (
                      <div className="flex items-center gap-1 text-xs text-slate-600">
                        <Briefcase className="w-3 h-3 text-slate-400"/>{c.current_title}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {c.current_stage && (
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${STAGE_COLORS[c.current_stage] || "bg-slate-100 text-slate-500"}`}>
                        {c.current_stage.replace(/_/g, " ")}
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                      {c.application_count}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-400 text-sm">
                  {search ? "No candidates match your search." : "No candidates found. Run a pipeline refresh."}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
