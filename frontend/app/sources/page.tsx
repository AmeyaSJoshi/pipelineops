"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import {
  Upload, Sheet, Building2, Users2, Briefcase, Globe,
  CheckCircle2, AlertCircle, Clock, Zap, RefreshCw,
  Lock, KeyRound, FileSpreadsheet,
} from "lucide-react";

// ── Source metadata ───────────────────────────────────────────────────────────

const SOURCE_META: Record<string, { icon: any; label: string; color: string; kind: "live" | "file" | "blocked" }> = {
  csv:           { icon: FileSpreadsheet, label: "CSV / Excel",   color: "text-blue-600",    kind: "file" },
  google_sheets: { icon: Sheet,           label: "Google Sheets", color: "text-green-600",   kind: "live" },
  greenhouse:    { icon: Building2,       label: "Greenhouse",    color: "text-emerald-600", kind: "live" },
  lever:         { icon: Users2,          label: "Lever",         color: "text-orange-500",  kind: "live" },
  bullhorn:      { icon: Briefcase,       label: "Bullhorn",      color: "text-purple-600",  kind: "live" },
  indeed:        { icon: Globe,           label: "Indeed",        color: "text-blue-500",    kind: "blocked" },
  careerbuilder: { icon: Globe,           label: "CareerBuilder", color: "text-red-500",     kind: "blocked" },
  monster:       { icon: Globe,           label: "Monster",       color: "text-violet-500",  kind: "blocked" },
  dice:          { icon: Globe,           label: "Dice",          color: "text-cyan-600",    kind: "blocked" },
};

const WORKAROUNDS: Record<string, string> = {
  indeed:        "Export candidates as CSV from your Indeed Employer dashboard.",
  careerbuilder: "Export candidates from CareerBuilder portal as CSV.",
  monster:       "Export from Monster Employer Center as CSV.",
  dice:          "Export candidate profiles from Dice employer account as CSV.",
};

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { cls: string; label: string }> = {
    connected:        { cls: "bg-emerald-100 text-emerald-700", label: "● Connected" },
    ready:            { cls: "bg-emerald-100 text-emerald-700", label: "● Ready" },
    needs_credentials:{ cls: "bg-amber-100  text-amber-700",   label: "Needs API Key" },
    blocked:          { cls: "bg-red-100    text-red-600",     label: "🚫 Blocked" },
    error:            { cls: "bg-red-100    text-red-600",     label: "Error" },
  };
  const { cls, label } = cfg[status] ?? { cls: "bg-slate-100 text-slate-500", label: status };
  return <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${cls}`}>{label}</span>;
}

// ── File upload zone ──────────────────────────────────────────────────────────

function FileUploadZone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<"idle" | "parsing" | "preview" | "importing" | "done" | "error">("idle");
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleFile(file: File) {
    setState("parsing");
    setError("");
    try {
      const result = await api.uploadFile(file, false);
      setPreview({ ...result, file });
      setState("preview");
    } catch (e: any) {
      setError(e.message || "Upload failed");
      setState("error");
    }
  }

  async function confirmImport() {
    if (!preview?.file) return;
    setState("importing");
    try {
      await api.uploadFile(preview.file, true);
      setState("done");
    } catch (e: any) {
      setError(e.message || "Import failed");
      setState("error");
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center">
          <FileSpreadsheet className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <span className="font-semibold text-sm text-slate-800">CSV / Excel Upload</span>
          <div className="text-[10px] text-slate-400 mt-0.5">.csv, .xlsx — no API key needed</div>
        </div>
        <div className="ml-auto">
          <StatusBadge status="ready" />
        </div>
      </div>

      {state === "idle" && (
        <div
          className="border-2 border-dashed border-slate-200 rounded-lg py-5 flex flex-col items-center gap-2 cursor-pointer hover:border-blue-300 hover:bg-blue-50/30 transition-colors"
          onClick={() => inputRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
        >
          <Upload className="w-5 h-5 text-slate-400" />
          <p className="text-xs text-slate-500">Drop a CSV or Excel file, or <span className="text-blue-600 underline">browse</span></p>
          <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" className="hidden"
            onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
        </div>
      )}

      {state === "parsing" && (
        <div className="py-4 flex items-center justify-center gap-2 text-xs text-slate-400">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Parsing file…
        </div>
      )}

      {state === "preview" && preview && (
        <div className="space-y-3">
          <div className="bg-slate-50 rounded-lg p-3 text-xs space-y-1.5">
            <div className="flex justify-between"><span className="text-slate-500">Format</span><span className="font-medium text-slate-700">{preview.format?.toUpperCase()}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Rows</span><span className="font-medium text-slate-700">{preview.candidates_found + preview.jobs_found} records</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Candidates</span><span className="font-medium text-slate-700">{preview.candidates_found}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Jobs</span><span className="font-medium text-slate-700">{preview.jobs_found}</span></div>
          </div>
          <div className="flex gap-2">
            <button onClick={confirmImport}
              className="flex-1 text-xs bg-blue-600 text-white rounded-md py-1.5 hover:bg-blue-700 transition-colors">
              Import {preview.candidates_found} records
            </button>
            <button onClick={() => { setState("idle"); setPreview(null); }}
              className="text-xs border border-slate-200 rounded-md px-3 py-1.5 text-slate-500 hover:bg-slate-50">
              Cancel
            </button>
          </div>
        </div>
      )}

      {state === "importing" && (
        <div className="py-4 flex items-center justify-center gap-2 text-xs text-slate-400">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Importing…
        </div>
      )}

      {state === "done" && (
        <div className="flex items-center gap-2 text-xs text-emerald-600 py-2">
          <CheckCircle2 className="w-4 h-4" /> Imported successfully.
          <button onClick={() => setState("idle")} className="ml-auto text-slate-400 underline">Upload another</button>
        </div>
      )}

      {state === "error" && (
        <div className="text-xs text-red-500 py-2 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5" /> {error}
          <button onClick={() => setState("idle")} className="ml-auto underline">Retry</button>
        </div>
      )}
    </div>
  );
}

// ── Live connector card ───────────────────────────────────────────────────────

function LiveConnectorCard({ src, onSync }: { src: any; onSync: (type: string) => void }) {
  const meta = SOURCE_META[src.source_type] ?? { icon: Globe, label: src.display_name, color: "text-slate-500", kind: "live" };
  const Icon = meta.icon;
  const isConnected = src.status === "connected";
  const needsCreds = src.status === "needs_credentials";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center">
            <Icon className={`w-4 h-4 ${meta.color}`} />
          </div>
          <span className="font-semibold text-sm text-slate-800">{meta.label}</span>
        </div>
        <StatusBadge status={src.status} />
      </div>

      <div className="space-y-1.5 text-xs text-slate-500">
        <div className="flex justify-between">
          <span>Last Sync</span>
          <span className="font-medium text-slate-700">
            {src.last_sync_at ? new Date(src.last_sync_at).toLocaleDateString() : "Never"}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Records</span>
          <span className="font-medium text-slate-700">{(src.records_total ?? 0).toLocaleString()}</span>
        </div>
      </div>

      <div className="pt-1 border-t border-slate-100">
        {isConnected ? (
          <button
            onClick={() => onSync(src.source_type)}
            className="w-full text-xs text-emerald-700 border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 rounded-md py-1.5 flex items-center justify-center gap-1.5"
          >
            <RefreshCw className="w-3 h-3" /> Sync Now
          </button>
        ) : needsCreds ? (
          <div className="flex items-center gap-1.5 text-[11px] text-amber-600">
            <KeyRound className="w-3.5 h-3.5" />
            <span>Set <code className="bg-amber-50 px-1 rounded">{src.source_type.toUpperCase()}_API_KEY</code> in .env</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// ── Blocked connector card ────────────────────────────────────────────────────

function BlockedConnectorCard({ src }: { src: any }) {
  const meta = SOURCE_META[src.source_type] ?? { icon: Globe, label: src.display_name, color: "text-slate-400", kind: "blocked" };
  const Icon = meta.icon;
  const workaround = WORKAROUNDS[src.source_type];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3 opacity-75">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center">
            <Icon className={`w-4 h-4 ${meta.color} opacity-50`} />
          </div>
          <span className="font-semibold text-sm text-slate-600">{meta.label}</span>
        </div>
        <StatusBadge status="blocked" />
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
        No official public API. {workaround}
      </p>

      <div className="pt-1 border-t border-slate-100">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
          <Lock className="w-3 h-3" />
          <span>Upload exported CSV via the CSV connector above</span>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Sources() {
  const [sources, setSources] = useState<any[]>([]);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncMsg, setSyncMsg] = useState("");

  useEffect(() => {
    api.sources()
      .then(d => { setSources(d.sources || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  async function handleSync(sourceType: string) {
    setSyncing(sourceType);
    setSyncMsg("");
    try {
      const result = await api.syncConnector(sourceType);
      if (result.job_id) {
        setSyncMsg(`Sync job started: ${result.job_id}`);
      } else {
        setSyncMsg(result.message || "Sync complete");
      }
      const d = await api.sources();
      setSources(d.sources || []);
    } catch (e: any) {
      setSyncMsg(`Sync failed: ${e.message}`);
    }
    setSyncing(null);
  }

  const liveSources = sources.filter(s => !["blocked"].includes(s.status) && s.source_type !== "csv");
  const blockedSources = sources.filter(s => s.status === "blocked");

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Connect ATS platforms, upload files, or manage blocked-state sources.
          </p>
        </div>
      </div>

      {/* AgentBox banner */}
      <div className="bg-slate-900 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-500 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-white font-semibold text-sm">GMI AgentBox Ready</span>
              <span className="text-[10px] bg-blue-500/30 text-blue-300 px-2 py-0.5 rounded-full font-semibold">BETA</span>
            </div>
            <p className="text-slate-400 text-xs mt-0.5">
              Real connectors for Greenhouse, Lever, Bullhorn, Google Sheets, and CSV/Excel.
              Blocked sources require official partner API access — see CONNECTOR_AUDIT.md.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-300 font-mono">AgentBox_v0.2</span>
        </div>
      </div>

      {syncMsg && (
        <div className="text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
          {syncMsg}
        </div>
      )}

      {/* File upload always first */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 mb-3">File Import</h2>
        <div className="grid grid-cols-3 gap-4">
          <FileUploadZone />
        </div>
      </div>

      {/* Live / needs-credentials connectors */}
      {liveSources.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-3">ATS & Platform Connectors</h2>
          <div className="grid grid-cols-3 gap-4">
            {liveSources.map(src => (
              <LiveConnectorCard key={src.id} src={src} onSync={handleSync} />
            ))}
          </div>
        </div>
      )}

      {/* Blocked sources */}
      {blockedSources.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-700 mb-1">Blocked Sources</h2>
          <p className="text-xs text-slate-400 mb-3">
            No official public API verified. Export CSV from the platform and upload above.
            See <code className="bg-slate-100 px-1 rounded">CONNECTOR_AUDIT.md</code> for details.
          </p>
          <div className="grid grid-cols-4 gap-3">
            {blockedSources.map(src => (
              <BlockedConnectorCard key={src.id} src={src} />
            ))}
          </div>
        </div>
      )}

      {!loading && sources.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <p className="text-sm">No sources found. Run <code className="bg-slate-100 px-1 rounded">POST /demo/seed</code> to populate.</p>
        </div>
      )}
    </div>
  );
}
