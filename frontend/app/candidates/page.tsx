"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Users, MapPin, Briefcase, RefreshCw, Search, X, ChevronRight,
  Mail, Phone, FileText, Zap, CheckCircle, AlertCircle
} from "lucide-react";

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

const ACTION_TYPES = [
  { type: "advance_stage", label: "Advance Stage", icon: ChevronRight },
  { type: "send_update", label: "Send Update", icon: Mail },
  { type: "schedule_interview", label: "Schedule Interview", icon: FileText },
  { type: "reject", label: "Reject", icon: X },
  { type: "make_offer", label: "Make Offer", icon: CheckCircle },
  { type: "request_references", label: "Request Refs", icon: FileText },
  { type: "reactivate", label: "Reactivate", icon: RefreshCw },
];

function StageBadge({ stage }: { stage?: string }) {
  if (!stage) return null;
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${STAGE_COLORS[stage] || "bg-slate-100 text-slate-500"}`}>
      {stage.replace(/_/g, " ")}
    </span>
  );
}

function ActionDrafter({
  candidateId,
  applicationId,
  stage,
}: {
  candidateId: number;
  applicationId?: number;
  stage?: string;
}) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [draft, setDraft] = useState<string | null>(null);
  const [isLlm, setIsLlm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const draft_action = useCallback(async (actionType: string) => {
    setSelectedAction(actionType);
    setDraft(null);
    setError(null);
    setLoading(true);
    try {
      const res = await api.draftAction({
        action_type: actionType,
        candidate_id: candidateId,
        context: { application_id: applicationId, current_stage: stage },
      });
      setDraft(res.draft_text || res.text || "No draft returned.");
      setIsLlm(res.source === "llm");
    } catch (e: any) {
      setError(e.message || "Draft failed.");
    } finally {
      setLoading(false);
    }
  }, [candidateId, applicationId, stage]);

  return (
    <div className="mt-4">
      <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-2">Draft Action</p>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {ACTION_TYPES.map(({ type, label }) => (
          <button
            key={type}
            onClick={() => draft_action(type)}
            className={`text-[11px] px-2.5 py-1 rounded-md border font-medium transition-colors ${
              selectedAction === type
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-slate-600 border-slate-200 hover:border-blue-300 hover:text-blue-600"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
          <RefreshCw className="w-3 h-3 animate-spin" /> Drafting…
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-red-500 text-xs py-2">
          <AlertCircle className="w-3 h-3" /> {error}
        </div>
      )}

      {draft && !loading && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
              {selectedAction?.replace(/_/g, " ")}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${isLlm ? "bg-violet-100 text-violet-600" : "bg-slate-100 text-slate-500"}`}>
              {isLlm ? "AI draft" : "template"}
            </span>
          </div>
          <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">{draft}</p>
          <button
            onClick={() => { navigator.clipboard.writeText(draft); }}
            className="mt-2 text-[10px] text-blue-500 hover:text-blue-700 font-medium"
          >
            Copy to clipboard
          </button>
        </div>
      )}
    </div>
  );
}

function CandidateSlideOut({
  candidateId,
  onClose,
}: {
  candidateId: number;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeApp, setActiveApp] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    api.candidate(candidateId)
      .then(d => {
        setDetail(d);
        const apps = d.applications || [];
        if (apps.length > 0) setActiveApp(apps[0].id);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [candidateId]);

  // close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const apps: any[] = detail?.applications || [];
  const selectedApp = apps.find((a: any) => a.id === activeApp);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed inset-y-0 right-0 w-[420px] max-w-full bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            {detail ? (
              <>
                <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-sm font-bold text-blue-700">
                  {detail.full_name?.charAt(0)?.toUpperCase() ?? "?"}
                </div>
                <div>
                  <p className="font-semibold text-slate-800 text-sm">{detail.full_name}</p>
                  {detail.current_title && (
                    <p className="text-xs text-slate-500">{detail.current_title}</p>
                  )}
                </div>
              </>
            ) : (
              <div className="h-9 w-36 bg-slate-100 rounded animate-pulse" />
            )}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm gap-2">
            <RefreshCw className="w-4 h-4 animate-spin" /> Loading profile…
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
            {/* Contact info */}
            <section>
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Contact</p>
              <div className="space-y-1.5">
                {detail.email_masked && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{detail.email_masked}</span>
                  </div>
                )}
                {detail.phone_masked && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{detail.phone_masked}</span>
                  </div>
                )}
                {detail.location && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{detail.location}</span>
                  </div>
                )}
                {detail.current_company && (
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{detail.current_company}</span>
                  </div>
                )}
              </div>
            </section>

            {/* Applications */}
            {apps.length > 0 && (
              <section>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  Applications ({apps.length})
                </p>
                <div className="space-y-1.5">
                  {apps.map((app: any) => (
                    <button
                      key={app.id}
                      onClick={() => setActiveApp(activeApp === app.id ? null : app.id)}
                      className={`w-full text-left flex items-start justify-between gap-2 px-3 py-2.5 rounded-lg border text-xs transition-colors ${
                        activeApp === app.id
                          ? "border-blue-300 bg-blue-50"
                          : "border-slate-100 bg-slate-50 hover:border-slate-200"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-slate-800 truncate">
                          {app.role_title || "Unknown Role"}
                        </p>
                        {app.company_name && (
                          <p className="text-slate-500 text-[11px]">{app.company_name}</p>
                        )}
                        {app.recruiter_owner && (
                          <p className="text-slate-400 text-[11px]">Rec: {app.recruiter_owner}</p>
                        )}
                      </div>
                      <div className="shrink-0 mt-0.5">
                        <StageBadge stage={app.canonical_stage} />
                      </div>
                    </button>
                  ))}
                </div>
              </section>
            )}

            {/* Action drafter for selected application */}
            {selectedApp && (
              <section className="border-t border-slate-100 pt-4">
                <div className="flex items-center gap-1.5 mb-2">
                  <Zap className="w-3.5 h-3.5 text-blue-500" />
                  <p className="text-[11px] font-semibold text-slate-600">
                    Actions for {selectedApp.role_title || "this application"}
                  </p>
                </div>
                <ActionDrafter
                  candidateId={detail.id}
                  applicationId={selectedApp.id}
                  stage={selectedApp.canonical_stage}
                />
              </section>
            )}

            {apps.length === 0 && (
              <p className="text-xs text-slate-400 py-4 text-center">No applications on record.</p>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    api.candidates().then(d => setCandidates(d.candidates || [])).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = candidates.filter(c =>
    !search ||
    c.full_name.toLowerCase().includes(search.toLowerCase()) ||
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
        <a
          href="/anomalies"
          className="text-xs text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-100 transition-colors"
        >
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
        <div className="flex items-center gap-2 text-slate-400 py-8">
          <RefreshCw className="w-4 h-4 animate-spin" />Loading candidates…
        </div>
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
                <tr
                  key={c.id}
                  onClick={() => setSelectedId(c.id)}
                  className={`border-b border-slate-50 cursor-pointer transition-colors ${
                    selectedId === c.id ? "bg-blue-50/60" : "hover:bg-slate-50/50"
                  }`}
                >
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
                        <MapPin className="w-3 h-3 text-slate-400" />{c.location}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {c.current_title && (
                      <div className="flex items-center gap-1 text-xs text-slate-600">
                        <Briefcase className="w-3 h-3 text-slate-400" />{c.current_title}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <StageBadge stage={c.current_stage} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                      {c.application_count}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400 text-sm">
                    {search ? "No candidates match your search." : "No candidates found. Run a pipeline refresh."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {selectedId !== null && (
        <CandidateSlideOut
          candidateId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
