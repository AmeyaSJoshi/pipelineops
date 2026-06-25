"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Briefcase, MapPin, DollarSign, Users, ChevronDown, ChevronRight,
  RefreshCw, TrendingUp, Search, AlertCircle
} from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  open: "bg-emerald-100 text-emerald-700",
  paused: "bg-amber-100 text-amber-700",
  closed: "bg-slate-100 text-slate-500",
  filled: "bg-blue-100 text-blue-700",
  unknown: "bg-slate-100 text-slate-400",
};

const STAGE_COLORS: Record<string, string> = {
  new_lead: "bg-slate-200 text-slate-600",
  applied: "bg-blue-100 text-blue-700",
  recruiter_screen: "bg-cyan-100 text-cyan-700",
  qualified: "bg-teal-100 text-teal-700",
  submitted_to_client: "bg-indigo-100 text-indigo-700",
  client_review: "bg-violet-100 text-violet-700",
  interview_scheduled: "bg-purple-100 text-purple-700",
  interview_completed: "bg-fuchsia-100 text-fuchsia-700",
  offer: "bg-orange-100 text-orange-700",
  placed: "bg-emerald-100 text-emerald-700",
  rejected: "bg-red-100 text-red-600",
  withdrawn: "bg-slate-100 text-slate-400",
};

function MiniBar({ label, count, max }: { label: string; count: number; max: number }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-slate-500 w-24 truncate">{label.replace(/_/g, " ")}</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full bg-blue-400 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-slate-600 font-medium w-6 text-right">{count}</span>
    </div>
  );
}

function RoleCandidatesPanel({ roleId }: { roleId: number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.roleCandidates(roleId)
      .then(setData)
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [roleId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-xs py-4 pl-12">
        <RefreshCw className="w-3.5 h-3.5 animate-spin" />Loading candidates…
      </div>
    );
  }
  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-500 text-xs py-4 pl-12">
        <AlertCircle className="w-3.5 h-3.5" />{error}
      </div>
    );
  }

  const candidates: any[] = data?.candidates || [];
  const analysis: any = data?.analysis;

  // stage breakdown
  const stageCounts: Record<string, number> = {};
  candidates.forEach((c: any) => {
    stageCounts[c.canonical_stage || "unknown"] = (stageCounts[c.canonical_stage || "unknown"] || 0) + 1;
  });
  const maxStageCount = Math.max(...Object.values(stageCounts), 1);

  return (
    <div className="px-5 pb-5 pt-3 bg-slate-50/60 border-t border-slate-100">
      {/* AI analysis */}
      {analysis && (
        <div className="mb-4 p-3 bg-white border border-violet-200 rounded-lg">
          <div className="flex items-center gap-1.5 mb-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-violet-500" />
            <span className="text-[11px] font-semibold text-violet-700 uppercase tracking-wide">AI Analysis</span>
            <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded font-medium ${
              analysis.source === "llm" ? "bg-violet-100 text-violet-600" : "bg-slate-100 text-slate-500"
            }`}>
              {analysis.source === "llm" ? "AI" : "template"}
            </span>
          </div>
          {analysis.pipeline_health && (
            <p className="text-xs text-slate-600 mb-1.5">{analysis.pipeline_health}</p>
          )}
          {analysis.narrative && (
            <p className="text-xs text-slate-700 leading-relaxed">{analysis.narrative}</p>
          )}
          {analysis.stage_breakdown && Object.keys(analysis.stage_breakdown).length > 0 && (
            <div className="mt-2 space-y-1">
              {Object.entries(analysis.stage_breakdown as Record<string, number>).map(([stage, cnt]) => (
                <MiniBar key={stage} label={stage} count={cnt} max={maxStageCount} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stage distribution when no AI analysis */}
      {!analysis && Object.keys(stageCounts).length > 0 && (
        <div className="mb-4">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Stage Breakdown</p>
          <div className="space-y-1.5">
            {Object.entries(stageCounts)
              .sort(([, a], [, b]) => b - a)
              .map(([stage, cnt]) => (
                <MiniBar key={stage} label={stage} count={cnt} max={candidates.length} />
              ))}
          </div>
        </div>
      )}

      {/* Candidate list */}
      {candidates.length === 0 ? (
        <p className="text-xs text-slate-400 py-2">No active candidates on this role.</p>
      ) : (
        <>
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2">
            Candidates ({candidates.length})
          </p>
          <div className="space-y-1.5">
            {candidates.map((c: any, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between bg-white border border-slate-100 rounded-lg px-3 py-2.5"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center text-[10px] font-bold text-blue-600 shrink-0">
                    {c.full_name?.charAt(0)?.toUpperCase() ?? "?"}
                  </div>
                  <div className="min-w-0">
                    <a
                      href="/candidates"
                      className="text-xs font-medium text-slate-800 hover:text-blue-600 truncate block"
                    >
                      {c.full_name}
                    </a>
                    {c.current_title && (
                      <p className="text-[10px] text-slate-400 truncate">{c.current_title}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {c.recruiter_owner && (
                    <span className="text-[10px] text-slate-400 hidden sm:block">{c.recruiter_owner}</span>
                  )}
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    STAGE_COLORS[c.canonical_stage] || "bg-slate-100 text-slate-500"
                  }`}>
                    {(c.canonical_stage || "unknown").replace(/_/g, " ")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function RoleRow({ role }: { role: any }) {
  const [expanded, setExpanded] = useState(false);

  const funnelItems = [
    { label: "Applicants", count: role.applicant_count, color: "text-slate-600" },
    { label: "Submitted", count: role.submitted_count, color: "text-indigo-600" },
    { label: "Interviews", count: role.interview_count, color: "text-purple-600" },
    { label: "Offers", count: role.offer_count, color: "text-orange-600" },
    { label: "Placed", count: role.placement_count, color: "text-emerald-600" },
  ];

  return (
    <div className="border-b border-slate-100 last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-5 py-4 hover:bg-slate-50/60 transition-colors"
      >
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-slate-400">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </div>

          {/* Role info */}
          <div className="flex-1 min-w-0 grid grid-cols-[1fr_auto] gap-x-4 items-start">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-slate-800 text-sm">{role.title}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${STATUS_COLORS[role.status] || "bg-slate-100 text-slate-500"}`}>
                  {role.status}
                </span>
                {role.openings_count > 1 && (
                  <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    {role.openings_count} openings
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                <span className="flex items-center gap-1 text-xs text-slate-500">
                  <Briefcase className="w-3 h-3" />{role.company_name}
                </span>
                {role.location && (
                  <span className="flex items-center gap-1 text-xs text-slate-500">
                    <MapPin className="w-3 h-3" />{role.location}
                  </span>
                )}
                {role.pay_display && (
                  <span className="flex items-center gap-1 text-xs text-slate-500">
                    <DollarSign className="w-3 h-3" />{role.pay_display}
                  </span>
                )}
                {role.recruiter_owner && (
                  <span className="text-xs text-slate-400">Rec: {role.recruiter_owner}</span>
                )}
              </div>
            </div>

            {/* Funnel numbers */}
            <div className="flex items-center gap-4 shrink-0">
              {funnelItems.map(({ label, count, color }) => (
                <div key={label} className="text-center hidden sm:block">
                  <div className={`text-sm font-bold ${color}`}>{count}</div>
                  <div className="text-[9px] text-slate-400 uppercase tracking-wide">{label}</div>
                </div>
              ))}
              <div className="text-center sm:hidden">
                <div className="flex items-center gap-1 text-xs text-slate-600">
                  <Users className="w-3 h-3" />{role.applicant_count}
                </div>
              </div>
            </div>
          </div>
        </div>
      </button>

      {expanded && <RoleCandidatesPanel roleId={role.id} />}
    </div>
  );
}

export default function RolesPage() {
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const load = useCallback(() => {
    setLoading(true);
    api.roles().then(d => setRoles(d.roles || [])).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = roles.filter(r => {
    const matchStatus = statusFilter === "all" || r.status === statusFilter;
    const q = search.toLowerCase();
    const matchSearch = !search ||
      r.title.toLowerCase().includes(q) ||
      r.company_name?.toLowerCase().includes(q) ||
      r.recruiter_owner?.toLowerCase().includes(q);
    return matchStatus && matchSearch;
  });

  const openCount = roles.filter(r => r.status === "open").length;
  const totalCandidates = roles.reduce((s, r) => s + r.applicant_count, 0);
  const totalPlacements = roles.reduce((s, r) => s + r.placement_count, 0);

  return (
    <div className="space-y-5 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Roles</h1>
          <p className="text-sm text-slate-500 mt-0.5">All open and historical positions with pipeline breakdown.</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 text-xs border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-lg text-slate-600 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />Refresh
        </button>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Open Roles", value: openCount },
          { label: "Total Candidates", value: totalCandidates },
          { label: "Placements", value: totalPlacements },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 px-5 py-4">
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</div>
            <div className="text-3xl font-bold text-slate-800 mt-0.5">{value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-2">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search roles…"
            className="text-xs text-slate-700 placeholder:text-slate-400 outline-none bg-transparent w-40"
          />
        </div>
        <div className="flex items-center gap-1">
          {["all", "open", "paused", "filled", "closed"].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`text-xs px-3 py-1.5 rounded-md border font-medium transition-colors ${
                statusFilter === s
                  ? "bg-slate-800 text-white border-slate-800"
                  : "bg-white text-slate-500 border-slate-200 hover:border-slate-300"
              }`}
            >
              {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Roles table */}
      {loading ? (
        <div className="flex items-center gap-2 text-slate-400 py-8">
          <RefreshCw className="w-4 h-4 animate-spin" />Loading roles…
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {/* Column headers */}
          <div className="px-5 py-2.5 bg-slate-50/70 border-b border-slate-100 flex items-center gap-3">
            <div className="w-4" />
            <div className="flex-1 text-xs text-slate-500 font-medium uppercase tracking-wide">Role / Company</div>
            <div className="flex items-center gap-4 shrink-0 pr-1">
              {["Applicants", "Submitted", "Interviews", "Offers", "Placed"].map(h => (
                <div key={h} className="text-[10px] text-slate-400 font-medium uppercase tracking-wide w-14 text-center hidden sm:block">
                  {h}
                </div>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <div className="px-5 py-10 text-center text-slate-400 text-sm">
              {search || statusFilter !== "all"
                ? "No roles match your filters."
                : "No roles found. Upload a CSV or connect an ATS."}
            </div>
          ) : (
            filtered.map(role => <RoleRow key={role.id} role={role} />)
          )}
        </div>
      )}
    </div>
  );
}
