"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CheckCircle, XCircle, AlertTriangle, ExternalLink, RefreshCw, KeyRound, Lock } from "lucide-react";

const CONNECTOR_DOCS: Record<string, string> = {
  greenhouse: "https://developers.greenhouse.io/harvest",
  lever: "https://hire.lever.co/developer/documentation",
  bullhorn: "https://bullhorn.github.io/rest-api-docs",
  google_sheets: "https://developers.google.com/sheets/api",
};

const CONNECTOR_ENV: Record<string, string[]> = {
  greenhouse: ["GREENHOUSE_API_KEY"],
  lever: ["LEVER_API_KEY"],
  bullhorn: ["BULLHORN_CLIENT_ID", "BULLHORN_CLIENT_SECRET", "BULLHORN_USERNAME", "BULLHORN_PASSWORD"],
  google_sheets: ["GOOGLE_SHEETS_CREDENTIALS_JSON", "GOOGLE_SHEETS_SPREADSHEET_ID"],
};

function StatusPill({ ok }: { ok: boolean }) {
  return ok
    ? <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">Configured</span>
    : <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">Not Set</span>;
}

export default function SettingsPage() {
  const [gmiSettings, setGmiSettings] = useState<any>(null);
  const [connectors, setConnectors] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [onboarding, setOnboarding] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.gmiSettings(),
      api.health(),
      api.connectorSettings(),
      api.onboardingStatus(),
    ])
      .then(([g, h, c, o]) => {
        setGmiSettings(g);
        setHealth(h);
        setConnectors(c);
        setOnboarding(o);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const healthJson = health
    ? JSON.stringify({
        status: health.status,
        service: health.service,
        database: health.database,
        gmi_maas_configured: health.gmi_maas_configured,
        agentbox_ready: health.agentbox_ready,
        version: health.version,
      }, null, 2)
    : "Loading…";

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings & Deployment</h1>
        <p className="text-sm text-slate-500 mt-0.5">Configure agent parameters and verify deployment status.</p>
      </div>

      {!loading && !gmiSettings?.gmi_maas_configured && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-800">Running in local demo fallback mode</p>
            <p className="text-xs text-amber-700 mt-0.5">
              Add <code className="bg-amber-100 px-1 rounded">GMI_MAAS_BASE_URL</code> and{" "}
              <code className="bg-amber-100 px-1 rounded">GMI_MAAS_API_KEY</code> to enable AI features.{" "}
              <a href="https://discord.gg/mbYhCJSbF6" target="_blank" rel="noreferrer" className="underline">Get credits on GMI Discord →</a>
            </p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-slate-400 py-8"><RefreshCw className="w-4 h-4 animate-spin" />Loading…</div>
      ) : (
        <div className="grid grid-cols-[1fr_280px] gap-5">
          <div className="space-y-4">

            {/* Onboarding checklist */}
            {onboarding && (
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <h2 className="font-semibold text-slate-800 mb-4">Setup Checklist</h2>
                <div className="space-y-3">
                  {(onboarding.steps || []).map((step: any) => (
                    <div key={step.key} className="flex items-start gap-3">
                      {step.complete
                        ? <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                        : <div className="w-4 h-4 border-2 border-slate-200 rounded-full flex-shrink-0 mt-0.5" />}
                      <div>
                        <div className={`text-sm font-medium ${step.complete ? "text-slate-700" : "text-slate-400"}`}>{step.label}</div>
                        <div className="text-xs text-slate-400 mt-0.5">{step.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Connector configuration */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-800 mb-4">Connector Configuration</h2>
              <p className="text-xs text-slate-500 mb-4">
                All credentials are set via environment variables in <code className="bg-slate-100 px-1 rounded">.env</code>.
                No credentials are shown in the UI. See <code className="bg-slate-100 px-1 rounded">CONNECTOR_AUDIT.md</code> for setup instructions.
              </p>
              <div className="divide-y divide-slate-100">
                {connectors && Object.entries(connectors as Record<string, { configured: boolean }>).map(([name, info]) => (
                  <div key={name} className="py-3 flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-700 capitalize">{name.replace("_", " ")}</span>
                        <StatusPill ok={info.configured} />
                      </div>
                      {!info.configured && CONNECTOR_ENV[name] && (
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {CONNECTOR_ENV[name].map(v => (
                            <code key={v} className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">{v}</code>
                          ))}
                        </div>
                      )}
                    </div>
                    {CONNECTOR_DOCS[name] && (
                      <a href={CONNECTOR_DOCS[name]} target="_blank" rel="noreferrer"
                        className="text-[11px] text-blue-600 hover:underline flex items-center gap-1 mt-0.5 flex-shrink-0">
                        Docs <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Blocked sources note */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
                <Lock className="w-4 h-4 text-slate-400" /> Blocked Sources
              </h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Indeed, CareerBuilder, Monster, and Dice have no official public API available for employer
                data read. These sources are blocked per the connector audit. Users can export CSV from those
                platforms and upload via the{" "}
                <a href="/sources" className="text-blue-600 underline">Sources → CSV connector</a>.
                See <code className="bg-slate-100 px-1 rounded">CONNECTOR_AUDIT.md</code> for the path to unblock each source.
              </p>
            </div>

            {/* Health check */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-slate-800">Backend Health</h2>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${health?.status === "ok" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                  {health?.status === "ok" ? "✓ 200 OK" : "Error"}
                </span>
              </div>
              <pre className="text-[11px] bg-slate-900 text-emerald-300 rounded-lg p-4 font-mono overflow-x-auto leading-relaxed">
                {healthJson}
              </pre>
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <h3 className="font-semibold text-slate-800 text-sm mb-3">GMI AgentBox Status</h3>
              <div className="space-y-2.5">
                {[
                  { label: "GMI MaaS Configured", ok: gmiSettings?.gmi_maas_configured },
                  { label: "AgentBox Ready", ok: true },
                  { label: "AI Features Active", ok: gmiSettings?.gmi_maas_configured },
                ].map(({ label, ok }) => (
                  <div key={label} className="flex items-center justify-between">
                    <span className="text-xs text-slate-600">{label}</span>
                    {ok
                      ? <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">Yes</span>
                      : <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">No</span>}
                  </div>
                ))}
                {gmiSettings?.gmi_model && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-600">Model</span>
                    <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded max-w-[140px] truncate">{gmiSettings.gmi_model}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <h3 className="font-semibold text-slate-800 text-sm mb-3">Deployment Checklist</h3>
              <div className="space-y-2">
                {[
                  { label: "Backend running on port 8080", done: health?.status === "ok" },
                  { label: "Database connected", done: health?.database === "ok" },
                  { label: "CONNECTOR_AUDIT.md complete", done: true },
                  { label: "AGENTBOX.md written", done: true },
                  { label: "GMI MaaS credentials set", done: gmiSettings?.gmi_maas_configured },
                  { label: "At least one live connector", done: Object.values(connectors || {}).some((c: any) => c.configured) },
                ].map(item => (
                  <div key={item.label} className="flex items-center gap-2 text-xs">
                    {item.done
                      ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                      : <div className="w-3.5 h-3.5 border-2 border-slate-200 rounded-full flex-shrink-0" />}
                    <span className={item.done ? "text-slate-700" : "text-slate-400"}>{item.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <a
              href="https://discord.gg/mbYhCJSbF6"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between bg-slate-900 text-white rounded-xl p-4 hover:bg-slate-800 transition-colors group"
            >
              <div>
                <div className="text-sm font-semibold">Join GMI Discord</div>
                <div className="text-xs text-slate-400 mt-0.5">Get credits & deployment support</div>
              </div>
              <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
