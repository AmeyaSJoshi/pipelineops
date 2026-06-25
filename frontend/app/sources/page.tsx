"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Upload, Building2, Users2, Briefcase, Globe,
  CheckCircle2, AlertCircle, RefreshCw,
  Lock, KeyRound, FileSpreadsheet, ChevronDown, ChevronUp,
  Zap, ExternalLink, Trash2, Sheet,
} from "lucide-react";

// ── Connector metadata ────────────────────────────────────────────────────────

const META: Record<string, { icon: any; label: string; color: string; docsUrl?: string }> = {
  greenhouse:    { icon: Building2,      label: "Greenhouse",    color: "text-emerald-600", docsUrl: "https://developers.greenhouse.io/harvest" },
  lever:         { icon: Users2,         label: "Lever",         color: "text-orange-500",  docsUrl: "https://hire.lever.co/developer/documentation" },
  bullhorn:      { icon: Briefcase,      label: "Bullhorn",      color: "text-purple-600",  docsUrl: "https://bullhorn.github.io/rest-api-docs" },
  google_sheets: { icon: Sheet,          label: "Google Sheets", color: "text-green-600",   docsUrl: "https://developers.google.com/workspace/guides/create-credentials" },
  indeed:        { icon: Globe,          label: "Indeed",        color: "text-blue-400" },
  careerbuilder: { icon: Globe,          label: "CareerBuilder", color: "text-red-400" },
  monster:       { icon: Globe,          label: "Monster",       color: "text-violet-400" },
  dice:          { icon: Globe,          label: "Dice",          color: "text-cyan-500" },
};

const WORKAROUNDS: Record<string, string> = {
  indeed:        "Export candidates from your Indeed Employer dashboard as CSV, then upload above.",
  careerbuilder: "Export candidates from the CareerBuilder portal as CSV, then upload above.",
  monster:       "Export from Monster Employer Center as CSV, then upload above.",
  dice:          "Export candidate profiles from your Dice employer account as CSV, then upload above.",
};

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    connected:         "bg-emerald-100 text-emerald-700",
    ready:             "bg-emerald-100 text-emerald-700",
    needs_credentials: "bg-amber-100 text-amber-700",
    error:             "bg-red-100 text-red-600",
    blocked:           "bg-slate-100 text-slate-500",
  };
  const labels: Record<string, string> = {
    connected:         "● Connected",
    ready:             "● Ready",
    needs_credentials: "Needs credentials",
    error:             "Connection error",
    blocked:           "No public API",
  };
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${map[status] ?? "bg-slate-100 text-slate-500"}`}>
      {labels[status] ?? status}
    </span>
  );
}

// ── File upload zone ──────────────────────────────────────────────────────────

function FileUploadZone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<"idle" | "parsing" | "preview" | "importing" | "done" | "error">("idle");
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleFile(file: File) {
    setState("parsing"); setError("");
    try {
      const result = await api.uploadFile(file, false);
      setPreview({ ...result, file });
      setState("preview");
    } catch (e: any) { setError(e.message || "Upload failed"); setState("error"); }
  }

  async function confirmImport() {
    if (!preview?.file) return;
    setState("importing");
    try {
      await api.uploadFile(preview.file, true);
      setState("done");
    } catch (e: any) { setError(e.message || "Import failed"); setState("error"); }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
          <FileSpreadsheet className="w-4.5 h-4.5 text-blue-600" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-slate-800 text-sm">CSV / Excel Upload</div>
          <div className="text-[11px] text-slate-400 mt-0.5">.csv or .xlsx — no credentials needed</div>
        </div>
        <StatusBadge status="ready" />
      </div>

      {state === "idle" && (
        <div
          className="border-2 border-dashed border-slate-200 rounded-lg py-6 flex flex-col items-center gap-2 cursor-pointer hover:border-blue-300 hover:bg-blue-50/20 transition-colors"
          onClick={() => inputRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
        >
          <Upload className="w-5 h-5 text-slate-400" />
          <p className="text-xs text-slate-500">Drop a file or <span className="text-blue-600 underline">browse</span></p>
          <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" className="hidden"
            onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
        </div>
      )}

      {state === "parsing" && (
        <div className="py-4 flex items-center justify-center gap-2 text-xs text-slate-400">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Reading file…
        </div>
      )}

      {state === "preview" && preview && (
        <div className="space-y-3">
          <div className="bg-slate-50 rounded-lg p-3 text-xs grid grid-cols-2 gap-y-1.5">
            <span className="text-slate-500">Format</span><span className="font-medium text-slate-700 text-right">{preview.format?.toUpperCase()}</span>
            <span className="text-slate-500">Candidates</span><span className="font-medium text-slate-700 text-right">{preview.candidates_found}</span>
            <span className="text-slate-500">Jobs</span><span className="font-medium text-slate-700 text-right">{preview.jobs_found}</span>
          </div>
          <div className="flex gap-2">
            <button onClick={confirmImport} className="flex-1 text-xs bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700 transition-colors font-medium">
              Import {preview.candidates_found + preview.jobs_found} records
            </button>
            <button onClick={() => { setState("idle"); setPreview(null); }}
              className="text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-500 hover:bg-slate-50">
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
        <div className="flex items-center gap-2 text-xs text-emerald-600">
          <CheckCircle2 className="w-4 h-4" /> Imported successfully.
          <button onClick={() => { setState("idle"); setPreview(null); }} className="ml-auto text-slate-400 underline text-[11px]">Upload another</button>
        </div>
      )}

      {state === "error" && (
        <div className="text-xs text-red-500 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5" />{error}
          <button onClick={() => setState("idle")} className="ml-auto underline">Retry</button>
        </div>
      )}
    </div>
  );
}

// ── Live connector card with inline credential form ───────────────────────────

function ConnectorCard({
  sourceType,
  initialStatus,
  onSynced,
}: {
  sourceType: string;
  initialStatus: string;
  onSynced: () => void;
}) {
  const meta = META[sourceType] ?? { icon: Globe, label: sourceType, color: "text-slate-500" };
  const Icon = meta.icon;

  const [status, setStatus] = useState(initialStatus);
  const [expanded, setExpanded] = useState(initialStatus === "needs_credentials" || initialStatus === "error");
  const [fields, setFields] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [syncMsg, setSyncMsg] = useState("");
  const [loadingFields, setLoadingFields] = useState(false);

  const loadFields = useCallback(async () => {
    if (fields.length > 0) return;
    setLoadingFields(true);
    try {
      const res = await api.connectorFields(sourceType);
      setFields(res.fields || []);
      const init: Record<string, string> = {};
      (res.fields || []).forEach((f: any) => { init[f.key] = ""; });
      setValues(init);
    } catch {}
    setLoadingFields(false);
  }, [sourceType, fields.length]);

  function toggle() {
    if (!expanded) loadFields();
    setExpanded(!expanded);
    setTestResult(null);
    setSyncMsg("");
  }

  async function handleSave() {
    setSaving(true);
    setTestResult(null);
    try {
      const res = await api.saveCredentials(sourceType, values);
      setTestResult(res.connection_test);
      setStatus(res.status);
      if (res.status === "connected") setExpanded(false);
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || "Save failed" });
    }
    setSaving(false);
  }

  async function handleSync() {
    setSyncing(true);
    setSyncMsg("");
    try {
      const res = await api.syncConnector(sourceType);
      setSyncMsg(res.job_id ? `Sync started (job ${res.job_id.slice(0, 8)}…)` : res.message || "Sync complete");
      onSynced();
    } catch (e: any) {
      setSyncMsg(`Error: ${e.message}`);
    }
    setSyncing(false);
  }

  async function handleDelete() {
    if (!confirm("Remove stored credentials for this connector?")) return;
    await api.deleteCredentials(sourceType);
    setStatus("needs_credentials");
    setValues(Object.fromEntries(fields.map(f => [f.key, ""])));
    setTestResult(null);
    setSyncMsg("");
    setExpanded(true);
  }

  const isConnected = status === "connected";
  const isError = status === "error";
  const needsCreds = status === "needs_credentials";

  return (
    <div className={`bg-white rounded-xl border transition-all ${
      isConnected ? "border-emerald-200" : isError ? "border-red-200" : "border-slate-200"
    }`}>
      {/* Header row */}
      <div className="flex items-center gap-3 p-4">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
          isConnected ? "bg-emerald-50 border border-emerald-100" : "bg-slate-50 border border-slate-200"
        }`}>
          <Icon className={`w-4 h-4 ${meta.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800 text-sm">{meta.label}</span>
            {meta.docsUrl && (
              <a href={meta.docsUrl} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-blue-500 transition-colors">
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
          {isConnected && <p className="text-[11px] text-emerald-600 mt-0.5">Credentials saved & verified</p>}
          {isError && <p className="text-[11px] text-red-500 mt-0.5">Connection failed — check credentials</p>}
          {needsCreds && <p className="text-[11px] text-amber-600 mt-0.5">Enter your credentials to connect</p>}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge status={status} />
          {isConnected && (
            <button onClick={handleDelete} className="text-slate-300 hover:text-red-400 transition-colors p-1">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
          <button onClick={toggle} className="text-slate-400 hover:text-slate-600 transition-colors p-1">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Sync button when connected */}
      {isConnected && !expanded && (
        <div className="px-4 pb-4">
          {syncMsg && (
            <p className={`text-[11px] mb-2 ${syncMsg.startsWith("Error") ? "text-red-500" : "text-emerald-600"}`}>{syncMsg}</p>
          )}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 flex items-center justify-center gap-1.5 font-medium disabled:opacity-60 transition-colors"
          >
            {syncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            {syncing ? "Syncing…" : "Sync Now"}
          </button>
        </div>
      )}

      {/* Credential form */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-4 space-y-3">
          {loadingFields ? (
            <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
              <RefreshCw className="w-3 h-3 animate-spin" /> Loading…
            </div>
          ) : (
            <>
              {fields.map(field => (
                <div key={field.key} className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">
                    {field.label}
                  </label>
                  {field.type === "textarea" ? (
                    <textarea
                      rows={5}
                      value={values[field.key] ?? ""}
                      onChange={e => setValues(v => ({ ...v, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-700 placeholder:text-slate-300 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100 font-mono resize-none"
                    />
                  ) : (
                    <input
                      type={field.type === "password" ? "password" : "text"}
                      value={values[field.key] ?? ""}
                      onChange={e => setValues(v => ({ ...v, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      autoComplete="off"
                      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-700 placeholder:text-slate-300 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"
                    />
                  )}
                  {field.help && (
                    <p className="text-[10px] text-slate-400 leading-relaxed">{field.help}</p>
                  )}
                </div>
              ))}

              {/* Connection test result */}
              {testResult && (
                <div className={`flex items-start gap-2 text-xs p-3 rounded-lg ${
                  testResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-600 border border-red-200"
                }`}>
                  {testResult.success
                    ? <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                    : <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />}
                  {testResult.message}
                </div>
              )}

              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleSave}
                  disabled={saving || fields.some(f => !values[f.key]?.trim())}
                  className="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 font-medium flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
                >
                  {saving ? <RefreshCw className="w-3 h-3 animate-spin" /> : <KeyRound className="w-3 h-3" />}
                  {saving ? "Saving & testing…" : "Save & test connection"}
                </button>
                {(isConnected || isError) && (
                  <button onClick={() => setExpanded(false)}
                    className="text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-500 hover:bg-slate-50">
                    Cancel
                  </button>
                )}
              </div>

              {isConnected && (
                <div className="pt-1">
                  {syncMsg && (
                    <p className={`text-[11px] mb-2 ${syncMsg.startsWith("Error") ? "text-red-500" : "text-emerald-600"}`}>{syncMsg}</p>
                  )}
                  <button
                    onClick={handleSync}
                    disabled={syncing}
                    className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 flex items-center justify-center gap-1.5 font-medium disabled:opacity-60 transition-colors"
                  >
                    {syncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                    {syncing ? "Syncing…" : "Sync Now"}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Blocked connector card ────────────────────────────────────────────────────

function BlockedCard({ sourceType }: { sourceType: string }) {
  const meta = META[sourceType] ?? { icon: Globe, label: sourceType, color: "text-slate-400" };
  const Icon = meta.icon;
  return (
    <div className="bg-white rounded-xl border border-slate-100 p-4 opacity-60">
      <div className="flex items-center gap-2.5 mb-2">
        <Icon className={`w-4 h-4 ${meta.color}`} />
        <span className="font-medium text-slate-600 text-sm">{meta.label}</span>
        <StatusBadge status="blocked" />
      </div>
      <p className="text-[11px] text-slate-400 leading-relaxed flex items-start gap-1">
        <Lock className="w-3 h-3 mt-0.5 shrink-0" />
        {WORKAROUNDS[sourceType] ?? "No official public API. Use CSV export."}
      </p>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

const LIVE_CONNECTOR_TYPES = ["greenhouse", "lever", "bullhorn", "google_sheets"];
const BLOCKED_TYPES = ["indeed", "careerbuilder", "monster", "dice"];

export default function Sources() {
  const [connectors, setConnectors] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    api.connectors()
      .then(d => { setConnectors(d.live || {}); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  function statusFor(type: string) {
    return connectors[type]?.status ?? "needs_credentials";
  }

  const connectedCount = LIVE_CONNECTOR_TYPES.filter(t => statusFor(t) === "connected").length;

  return (
    <div className="space-y-7 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Connect your ATS and import candidate data. Credentials are encrypted and stored securely.
        </p>
      </div>

      {/* Status strip */}
      <div className="flex items-center gap-3 bg-slate-900 rounded-xl px-4 py-3">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-white text-sm font-medium">
            {connectedCount === 0
              ? "No live connectors connected yet"
              : `${connectedCount} connector${connectedCount > 1 ? "s" : ""} connected`}
          </p>
          <p className="text-slate-400 text-[11px]">
            Enter credentials below to sync directly from your ATS — no .env editing required.
          </p>
        </div>
        {connectedCount > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] text-emerald-400 font-medium">Live</span>
          </div>
        )}
      </div>

      {/* File upload */}
      <section>
        <h2 className="text-sm font-semibold text-slate-700 mb-3">File Import</h2>
        <FileUploadZone />
      </section>

      {/* Live connectors */}
      <section>
        <h2 className="text-sm font-semibold text-slate-700 mb-1">ATS Connectors</h2>
        <p className="text-xs text-slate-400 mb-3">
          Enter your API credentials once — they're encrypted and saved so you never need to re-enter them.
        </p>
        {loading ? (
          <div className="flex items-center gap-2 text-slate-400 text-sm py-4">
            <RefreshCw className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : (
          <div className="space-y-3">
            {LIVE_CONNECTOR_TYPES.map(type => (
              <ConnectorCard
                key={type}
                sourceType={type}
                initialStatus={statusFor(type)}
                onSynced={load}
              />
            ))}
          </div>
        )}
      </section>

      {/* Blocked sources */}
      <section>
        <h2 className="text-sm font-semibold text-slate-700 mb-1">Unavailable Sources</h2>
        <p className="text-xs text-slate-400 mb-3">
          These platforms don't offer an official public API. Export a CSV from each platform and upload it above.
        </p>
        <div className="grid grid-cols-2 gap-3">
          {BLOCKED_TYPES.map(type => (
            <BlockedCard key={type} sourceType={type} />
          ))}
        </div>
      </section>
    </div>
  );
}
