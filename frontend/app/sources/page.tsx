"use client";
import { useEffect, useRef, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import {
  Upload, Building2, Users2, Briefcase, Globe, Sheet,
  CheckCircle2, AlertCircle, RefreshCw, Lock,
  FileSpreadsheet, ChevronDown, ChevronUp,
  Zap, ExternalLink, Trash2, LogIn,
} from "lucide-react";

// ── Connector metadata ────────────────────────────────────────────────────────

interface ConnectorMeta {
  icon: any;
  label: string;
  color: string;
  /** Deep link to the exact settings page where the API key lives */
  keyUrl?: string;
  keyUrlLabel?: string;
  /** Step-by-step hint shown under the key URL */
  keyHint?: string;
}

const META: Record<string, ConnectorMeta> = {
  greenhouse: {
    icon: Building2,
    label: "Greenhouse",
    color: "text-emerald-600",
    keyUrl: "https://app.greenhouse.io/configure/dev_center/credentials",
    keyUrlLabel: "Open Greenhouse API credentials →",
    keyHint: "Configure → Dev Center → API Credential Management → Create New Credential → choose Harvest",
  },
  lever: {
    icon: Users2,
    label: "Lever",
    color: "text-orange-500",
    keyUrl: "https://hire.lever.co/settings/integrations",
    keyUrlLabel: "Open Lever integrations settings →",
    keyHint: "Settings → Integrations & API → API Credentials → Generate New Key",
  },
  bullhorn: {
    icon: Briefcase,
    label: "Bullhorn",
    color: "text-purple-600",
    keyUrl: "https://www.bullhorn.com/platform/api/",
    keyUrlLabel: "Request Bullhorn API access →",
    keyHint: "Bullhorn issues client credentials to registered API partners. Click above to start the request, then enter the four values you receive.",
  },
  google_sheets: {
    icon: Sheet,
    label: "Google Sheets",
    color: "text-green-600",
    keyUrl: "https://console.cloud.google.com/apis/credentials",
    keyUrlLabel: "Open Google Cloud credentials →",
    keyHint: "Create an OAuth 2.0 Client ID (Web application). Add http://localhost:8080/connectors/google_sheets/oauth/callback as an authorized redirect URI.",
  },
  indeed:        { icon: Globe, label: "Indeed",        color: "text-blue-400" },
  careerbuilder: { icon: Globe, label: "CareerBuilder", color: "text-red-400" },
  monster:       { icon: Globe, label: "Monster",       color: "text-violet-400" },
  dice:          { icon: Globe, label: "Dice",          color: "text-cyan-500" },
};

const BLOCKED_WORKAROUNDS: Record<string, string> = {
  indeed:        "Export candidates from your Indeed Employer dashboard as CSV, then upload above.",
  careerbuilder: "Export candidates from the CareerBuilder portal as CSV, then upload above.",
  monster:       "Export from Monster Employer Center as CSV, then upload above.",
  dice:          "Export candidate profiles from your Dice employer account as CSV, then upload above.",
};

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
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
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${styles[status] ?? "bg-slate-100 text-slate-500"}`}>
      {labels[status] ?? status}
    </span>
  );
}

// ── File upload zone ──────────────────────────────────────────────────────────

function FileUploadZone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<"idle"|"parsing"|"preview"|"importing"|"done"|"error">("idle");
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleFile(file: File) {
    setState("parsing"); setError("");
    try { setPreview({ ...(await api.uploadFile(file, false)), file }); setState("preview"); }
    catch (e: any) { setError(e.message || "Upload failed"); setState("error"); }
  }
  async function confirmImport() {
    if (!preview?.file) return;
    setState("importing");
    try { await api.uploadFile(preview.file, true); setState("done"); }
    catch (e: any) { setError(e.message || "Import failed"); setState("error"); }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0">
          <FileSpreadsheet className="w-4 h-4 text-blue-600" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-slate-800 text-sm">CSV / Excel Upload</div>
          <div className="text-[11px] text-slate-400">.csv or .xlsx — no credentials needed</div>
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
      {state === "parsing" && <div className="py-4 flex items-center justify-center gap-2 text-xs text-slate-400"><RefreshCw className="w-3.5 h-3.5 animate-spin"/>Reading file…</div>}
      {state === "preview" && preview && (
        <div className="space-y-3">
          <div className="bg-slate-50 rounded-lg p-3 text-xs grid grid-cols-2 gap-y-1.5">
            <span className="text-slate-500">Format</span><span className="font-medium text-slate-700 text-right">{preview.format?.toUpperCase()}</span>
            <span className="text-slate-500">Candidates</span><span className="font-medium text-slate-700 text-right">{preview.candidates_found}</span>
            <span className="text-slate-500">Jobs</span><span className="font-medium text-slate-700 text-right">{preview.jobs_found}</span>
          </div>
          <div className="flex gap-2">
            <button onClick={confirmImport} className="flex-1 text-xs bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700 font-medium transition-colors">
              Import {preview.candidates_found + preview.jobs_found} records
            </button>
            <button onClick={() => { setState("idle"); setPreview(null); }} className="text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-500 hover:bg-slate-50">Cancel</button>
          </div>
        </div>
      )}
      {state === "importing" && <div className="py-4 flex items-center justify-center gap-2 text-xs text-slate-400"><RefreshCw className="w-3.5 h-3.5 animate-spin"/>Importing…</div>}
      {state === "done" && (
        <div className="flex items-center gap-2 text-xs text-emerald-600">
          <CheckCircle2 className="w-4 h-4"/>Imported successfully.
          <button onClick={() => { setState("idle"); setPreview(null); }} className="ml-auto text-slate-400 underline text-[11px]">Upload another</button>
        </div>
      )}
      {state === "error" && (
        <div className="text-xs text-red-500 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5"/>{error}
          <button onClick={() => setState("idle")} className="ml-auto underline">Retry</button>
        </div>
      )}
    </div>
  );
}

// ── Google Sheets connector (OAuth flow) ──────────────────────────────────────

function GoogleSheetsCard({ initialStatus, onSynced }: { initialStatus: string; onSynced: () => void }) {
  const meta = META.google_sheets;
  const Icon = meta.icon;

  const [status, setStatus] = useState(initialStatus);
  const [expanded, setExpanded] = useState(initialStatus !== "connected");
  const [values, setValues] = useState({ oauth_client_id: "", oauth_client_secret: "", spreadsheet_id: "" });
  const [saving, setSaving] = useState(false);
  const [savedOk, setSavedOk] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");
  const [saveError, setSaveError] = useState("");

  const isConnected = status === "connected";
  const canSignIn = savedOk || isConnected;

  async function handleSaveAndSignIn() {
    setSaving(true); setSaveError("");
    try {
      // Save client_id + client_secret + spreadsheet_id encrypted
      await api.saveCredentials("google_sheets", values);
      setSavedOk(true);
      // Get the OAuth URL and redirect
      const { url } = await api.googleOAuthUrl();
      window.location.href = url;
    } catch (e: any) {
      setSaveError(e.message || "Failed to save credentials");
    }
    setSaving(false);
  }

  async function handleSignInOnly() {
    try {
      const { url } = await api.googleOAuthUrl();
      window.location.href = url;
    } catch (e: any) {
      setSaveError(e.message || "Failed to get auth URL");
    }
  }

  async function handleSync() {
    setSyncing(true); setSyncMsg("");
    try {
      const res = await api.syncConnector("google_sheets");
      setSyncMsg(res.job_id ? `Sync started` : res.message || "Sync complete");
      onSynced();
    } catch (e: any) { setSyncMsg(`Error: ${e.message}`); }
    setSyncing(false);
  }

  async function handleDelete() {
    if (!confirm("Disconnect Google Sheets?")) return;
    await api.deleteCredentials("google_sheets");
    setStatus("needs_credentials"); setSavedOk(false); setExpanded(true); setSyncMsg("");
  }

  return (
    <div className={`bg-white rounded-xl border transition-all ${isConnected ? "border-emerald-200" : status === "error" ? "border-red-200" : "border-slate-200"}`}>
      {/* Header */}
      <div className="flex items-center gap-3 p-4">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${isConnected ? "bg-emerald-50 border border-emerald-100" : "bg-slate-50 border border-slate-200"}`}>
          <Icon className={`w-4 h-4 ${meta.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <span className="font-semibold text-slate-800 text-sm">Google Sheets</span>
          {isConnected
            ? <p className="text-[11px] text-emerald-600 mt-0.5">Connected via Google OAuth</p>
            : <p className="text-[11px] text-amber-600 mt-0.5">Sign in with Google to connect</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={status} />
          {isConnected && <button onClick={handleDelete} className="text-slate-300 hover:text-red-400 p-1"><Trash2 className="w-3.5 h-3.5"/></button>}
          <button onClick={() => setExpanded(!expanded)} className="text-slate-400 hover:text-slate-600 p-1">
            {expanded ? <ChevronUp className="w-4 h-4"/> : <ChevronDown className="w-4 h-4"/>}
          </button>
        </div>
      </div>

      {/* Sync button when connected and collapsed */}
      {isConnected && !expanded && (
        <div className="px-4 pb-4 space-y-2">
          {syncMsg && <p className={`text-[11px] ${syncMsg.startsWith("Error") ? "text-red-500" : "text-emerald-600"}`}>{syncMsg}</p>}
          <button onClick={handleSync} disabled={syncing} className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 flex items-center justify-center gap-1.5 font-medium disabled:opacity-60 transition-colors">
            {syncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin"/> : <RefreshCw className="w-3.5 h-3.5"/>}
            {syncing ? "Syncing…" : "Sync Now"}
          </button>
        </div>
      )}

      {/* Setup form */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-4 space-y-4">
          {/* Step 1: get credentials from Google Cloud */}
          <div className="bg-slate-50 rounded-lg p-3 space-y-2">
            <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">Step 1 — Get OAuth credentials from Google</p>
            <a href={meta.keyUrl} target="_blank" rel="noreferrer"
              className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium">
              <ExternalLink className="w-3.5 h-3.5 shrink-0"/>
              {meta.keyUrlLabel}
            </a>
            <p className="text-[10px] text-slate-500 leading-relaxed">{meta.keyHint}</p>
          </div>

          {/* Step 2: enter credentials */}
          <div className="space-y-3">
            <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">Step 2 — Enter your credentials</p>
            {[
              { key: "oauth_client_id", label: "OAuth Client ID", type: "text", placeholder: "123456789-abc.apps.googleusercontent.com" },
              { key: "oauth_client_secret", label: "OAuth Client Secret", type: "password", placeholder: "GOCSPX-…" },
              { key: "spreadsheet_id", label: "Spreadsheet ID", type: "text", placeholder: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
                help: "The ID from your Google Sheets URL: …/spreadsheets/d/[THIS_PART]/edit" },
            ].map(f => (
              <div key={f.key} className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">{f.label}</label>
                <input type={f.type} value={(values as any)[f.key]} placeholder={f.placeholder} autoComplete="off"
                  onChange={e => setValues(v => ({ ...v, [f.key]: e.target.value }))}
                  className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-700 placeholder:text-slate-300 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"/>
                {f.help && <p className="text-[10px] text-slate-400">{f.help}</p>}
              </div>
            ))}
          </div>

          {saveError && (
            <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-2.5">
              <AlertCircle className="w-3.5 h-3.5 shrink-0"/>{saveError}
            </div>
          )}

          {/* Step 3: sign in */}
          <div className="space-y-2">
            <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">Step 3 — Authorize</p>
            {!isConnected ? (
              <button
                onClick={handleSaveAndSignIn}
                disabled={saving || !values.oauth_client_id || !values.oauth_client_secret || !values.spreadsheet_id}
                className="w-full flex items-center justify-center gap-2 text-sm font-medium bg-white border border-slate-300 hover:border-blue-400 hover:bg-blue-50/30 text-slate-700 rounded-lg py-2.5 disabled:opacity-50 transition-colors shadow-sm"
              >
                {saving ? <RefreshCw className="w-4 h-4 animate-spin"/> : (
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                )}
                {saving ? "Saving & redirecting…" : "Sign in with Google"}
              </button>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-lg p-2.5">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0"/>Connected via Google OAuth
                </div>
                <button onClick={handleSignInOnly} className="w-full text-xs text-slate-500 border border-slate-200 rounded-lg py-2 hover:bg-slate-50">Re-authorize</button>
              </div>
            )}
          </div>

          {isConnected && (
            <button onClick={handleSync} disabled={syncing}
              className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 flex items-center justify-center gap-1.5 font-medium disabled:opacity-60 transition-colors">
              {syncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin"/> : <RefreshCw className="w-3.5 h-3.5"/>}
              {syncing ? "Syncing…" : "Sync Now"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── ATS connector card (API key with deep link) ───────────────────────────────

function ATSConnectorCard({ sourceType, initialStatus, onSynced }: { sourceType: string; initialStatus: string; onSynced: () => void }) {
  const meta = META[sourceType] ?? { icon: Globe, label: sourceType, color: "text-slate-500" };
  const Icon = meta.icon;

  const [status, setStatus] = useState(initialStatus);
  const [expanded, setExpanded] = useState(initialStatus !== "connected");
  const [fields, setFields] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [syncMsg, setSyncMsg] = useState("");

  const loadFields = useCallback(async () => {
    if (fields.length > 0) return;
    try {
      const res = await api.connectorFields(sourceType);
      setFields(res.fields || []);
      setValues(Object.fromEntries((res.fields || []).map((f: any) => [f.key, ""])));
    } catch {}
  }, [sourceType, fields.length]);

  function toggle() { if (!expanded) loadFields(); setExpanded(!expanded); setTestResult(null); }

  async function handleSave() {
    setSaving(true); setTestResult(null);
    try {
      const res = await api.saveCredentials(sourceType, values);
      setTestResult(res.connection_test);
      setStatus(res.status);
      if (res.status === "connected") setExpanded(false);
    } catch (e: any) { setTestResult({ success: false, message: e.message || "Save failed" }); }
    setSaving(false);
  }

  async function handleSync() {
    setSyncing(true); setSyncMsg("");
    try {
      const res = await api.syncConnector(sourceType);
      setSyncMsg(res.job_id ? `Sync started (job ${res.job_id.slice(0, 8)}…)` : res.message || "Done");
      onSynced();
    } catch (e: any) { setSyncMsg(`Error: ${e.message}`); }
    setSyncing(false);
  }

  async function handleDelete() {
    if (!confirm(`Remove stored credentials for ${meta.label}?`)) return;
    await api.deleteCredentials(sourceType);
    setStatus("needs_credentials");
    setValues(Object.fromEntries(fields.map(f => [f.key, ""])));
    setTestResult(null); setSyncMsg(""); setExpanded(true);
  }

  const isConnected = status === "connected";
  const isError = status === "error";

  return (
    <div className={`bg-white rounded-xl border transition-all ${isConnected ? "border-emerald-200" : isError ? "border-red-200" : "border-slate-200"}`}>
      {/* Header */}
      <div className="flex items-center gap-3 p-4">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${isConnected ? "bg-emerald-50 border border-emerald-100" : "bg-slate-50 border border-slate-200"}`}>
          <Icon className={`w-4 h-4 ${meta.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <span className="font-semibold text-slate-800 text-sm">{meta.label}</span>
          {isConnected
            ? <p className="text-[11px] text-emerald-600 mt-0.5">API key verified & saved</p>
            : isError
            ? <p className="text-[11px] text-red-500 mt-0.5">Connection failed — check your key</p>
            : <p className="text-[11px] text-amber-600 mt-0.5">Enter your API key to connect</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <StatusBadge status={status}/>
          {(isConnected || isError) && (
            <button onClick={handleDelete} className="text-slate-300 hover:text-red-400 p-1"><Trash2 className="w-3.5 h-3.5"/></button>
          )}
          <button onClick={toggle} className="text-slate-400 hover:text-slate-600 p-1">
            {expanded ? <ChevronUp className="w-4 h-4"/> : <ChevronDown className="w-4 h-4"/>}
          </button>
        </div>
      </div>

      {/* Sync button when connected and collapsed */}
      {isConnected && !expanded && (
        <div className="px-4 pb-4 space-y-2">
          {syncMsg && <p className={`text-[11px] ${syncMsg.startsWith("Error") ? "text-red-500" : "text-emerald-600"}`}>{syncMsg}</p>}
          <button onClick={handleSync} disabled={syncing} className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 flex items-center justify-center gap-1.5 font-medium disabled:opacity-60 transition-colors">
            {syncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin"/> : <RefreshCw className="w-3.5 h-3.5"/>}
            {syncing ? "Syncing…" : "Sync Now"}
          </button>
        </div>
      )}

      {/* Credential form */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-4 space-y-4">
          {/* Deep link to settings page */}
          {meta.keyUrl && (
            <div className="bg-slate-50 rounded-lg p-3 space-y-1.5">
              <a href={meta.keyUrl} target="_blank" rel="noreferrer"
                className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium">
                <ExternalLink className="w-3.5 h-3.5 shrink-0"/>{meta.keyUrlLabel}
              </a>
              {meta.keyHint && <p className="text-[10px] text-slate-500 leading-relaxed">{meta.keyHint}</p>}
            </div>
          )}

          {/* Fields */}
          <div className="space-y-3">
            {fields.map(field => (
              <div key={field.key} className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">{field.label}</label>
                <input
                  type={field.type === "password" ? "password" : "text"}
                  value={values[field.key] ?? ""}
                  onChange={e => setValues(v => ({ ...v, [field.key]: e.target.value }))}
                  placeholder={field.placeholder}
                  autoComplete="off"
                  className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-700 placeholder:text-slate-300 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"
                />
                {field.help && <p className="text-[10px] text-slate-400 leading-relaxed">{field.help}</p>}
              </div>
            ))}

            {fields.length === 0 && (
              <div className="text-xs text-slate-400 py-2 flex items-center gap-2">
                <RefreshCw className="w-3 h-3 animate-spin"/>Loading…
              </div>
            )}
          </div>

          {/* Test result */}
          {testResult && (
            <div className={`flex items-start gap-2 text-xs p-3 rounded-lg ${testResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-600 border border-red-200"}`}>
              {testResult.success ? <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0"/> : <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0"/>}
              {testResult.message}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving || fields.some(f => !values[f.key]?.trim())}
              className="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 font-medium flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
            >
              {saving ? <RefreshCw className="w-3 h-3 animate-spin"/> : <LogIn className="w-3 h-3"/>}
              {saving ? "Saving & testing…" : "Save & test connection"}
            </button>
            {(isConnected || isError) && (
              <button onClick={() => setExpanded(false)} className="text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-500 hover:bg-slate-50">Cancel</button>
            )}
          </div>

          {isConnected && (
            <button onClick={handleSync} disabled={syncing}
              className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-2 flex items-center justify-center gap-1.5 font-medium disabled:opacity-60 transition-colors">
              {syncing ? <RefreshCw className="w-3.5 h-3.5 animate-spin"/> : <RefreshCw className="w-3.5 h-3.5"/>}
              {syncing ? "Syncing…" : "Sync Now"}
            </button>
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
        <Icon className={`w-4 h-4 ${meta.color}`}/>
        <span className="font-medium text-slate-600 text-sm">{meta.label}</span>
        <StatusBadge status="blocked"/>
      </div>
      <p className="text-[11px] text-slate-400 leading-relaxed flex items-start gap-1.5">
        <Lock className="w-3 h-3 mt-0.5 shrink-0"/>
        {BLOCKED_WORKAROUNDS[sourceType] ?? "No official public API. Use CSV export."}
      </p>
    </div>
  );
}

// ── OAuth callback handler ────────────────────────────────────────────────────

function OAuthNotice() {
  const params = useSearchParams();
  const connected = params.get("connected");
  const oauthError = params.get("oauth_error");

  if (!connected && !oauthError) return null;

  return (
    <div className={`flex items-center gap-2.5 text-sm px-4 py-3 rounded-xl border ${
      connected ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-red-50 border-red-200 text-red-700"
    }`}>
      {connected
        ? <><CheckCircle2 className="w-4 h-4 shrink-0"/><span>Google Sheets connected successfully.</span></>
        : <><AlertCircle className="w-4 h-4 shrink-0"/><span>Google sign-in failed: {oauthError}</span></>}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

const ATS_TYPES = ["greenhouse", "lever", "bullhorn"];
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

  const connectedCount = [...ATS_TYPES, "google_sheets"].filter(t => statusFor(t) === "connected").length;

  return (
    <div className="space-y-7 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Connect your ATS or upload a file. Credentials are encrypted at rest.
        </p>
      </div>

      {/* OAuth result banner */}
      <Suspense>
        <OAuthNotice/>
      </Suspense>

      {/* Status strip */}
      <div className="flex items-center gap-3 bg-slate-900 rounded-xl px-4 py-3">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shrink-0">
          <Zap className="w-4 h-4 text-white"/>
        </div>
        <div className="flex-1">
          <p className="text-white text-sm font-medium">
            {connectedCount === 0 ? "No live connectors connected yet" : `${connectedCount} connector${connectedCount > 1 ? "s" : ""} connected`}
          </p>
          <p className="text-slate-400 text-[11px]">Credentials are saved once — no .env files needed.</p>
        </div>
        {connectedCount > 0 && <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"/><span className="text-[11px] text-emerald-400 font-medium">Live</span></div>}
      </div>

      {/* File upload */}
      <section>
        <h2 className="text-sm font-semibold text-slate-700 mb-3">File Import</h2>
        <FileUploadZone/>
      </section>

      {/* ATS connectors */}
      <section>
        <h2 className="text-sm font-semibold text-slate-700 mb-1">ATS Connectors</h2>
        <p className="text-xs text-slate-400 mb-3">Click a connector to open the setup form. Credentials are encrypted and stored so you only enter them once.</p>
        {loading ? (
          <div className="flex items-center gap-2 text-slate-400 text-sm py-4"><RefreshCw className="w-4 h-4 animate-spin"/>Loading…</div>
        ) : (
          <div className="space-y-3">
            {ATS_TYPES.map(type => (
              <ATSConnectorCard key={type} sourceType={type} initialStatus={statusFor(type)} onSynced={load}/>
            ))}
            <GoogleSheetsCard initialStatus={statusFor("google_sheets")} onSynced={load}/>
          </div>
        )}
      </section>

      {/* Blocked */}
      <section>
        <h2 className="text-sm font-semibold text-slate-700 mb-1">Unavailable Sources</h2>
        <p className="text-xs text-slate-400 mb-3">No official public API — export a CSV from each platform and upload it above.</p>
        <div className="grid grid-cols-2 gap-3">
          {BLOCKED_TYPES.map(type => <BlockedCard key={type} sourceType={type}/>)}
        </div>
      </section>
    </div>
  );
}
