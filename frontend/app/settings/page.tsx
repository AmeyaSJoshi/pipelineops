"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CheckCircle, XCircle, Eye, EyeOff, AlertTriangle, ExternalLink } from "lucide-react";

export default function SettingsPage() {
  const [gmiSettings, setGmiSettings] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.gmiSettings(), api.health()])
      .then(([g, h]) => { setGmiSettings(g); setHealth(h); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const healthJson = health ? JSON.stringify({
    status: health.status,
    service: health.service,
    database: health.database,
    gmi_maas_configured: health.gmi_maas_configured,
    agentbox_ready: health.agentbox_ready,
    version: health.version,
  }, null, 2) : "Loading…";

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings & Deployment</h1>
        <p className="text-sm text-slate-500 mt-0.5">Configure agent parameters and verify deployment status.</p>
      </div>

      {/* Warning banner */}
      {!loading && !gmiSettings?.gmi_maas_configured && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-800">Running in local demo fallback mode</p>
            <p className="text-xs text-amber-700 mt-0.5">Add GMI API Key to enable hosted model calls. See the <a href="https://discord.gg/mbYhCJSbF6" target="_blank" rel="noreferrer" className="underline">GMI Discord</a> for credits.</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-[1fr_280px] gap-5">
        {/* Left — settings */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-800 mb-4">General Settings</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">GMI API Key</label>
                <div className="relative">
                  <input
                    type={showKey ? "text" : "password"}
                    placeholder="gmk-…"
                    defaultValue={gmiSettings?.gmi_maas_configured ? "••••••••••••" : ""}
                    className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 pr-10 bg-slate-50 text-slate-700 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                  />
                  <button onClick={() => setShowKey(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Required for full agent capability.</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Organization ID</label>
                <input
                  type="text"
                  placeholder="org_7392a89"
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                />
              </div>
              <button className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg transition-colors font-medium">
                Save Configuration
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-slate-800">Backend Health</h2>
              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${health?.status === "ok" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                Status {health?.status === "ok" ? "200 OK" : "Error"}
              </span>
            </div>
            <pre className="text-[11px] bg-slate-900 text-emerald-300 rounded-lg p-4 font-mono overflow-x-auto leading-relaxed">
              {healthJson}
            </pre>
          </div>
        </div>

        {/* Right — GMI status */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-800 text-sm mb-3">GMI AgentBox Status</h3>
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600">GMI MaaS Configured</span>
                {gmiSettings?.gmi_maas_configured
                  ? <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">Yes</span>
                  : <span className="text-[11px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded">No</span>
                }
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600">AgentBox Ready</span>
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">Yes</span>
              </div>
              {gmiSettings?.gmi_model && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-600">Selected Model</span>
                  <span className="text-[11px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded">{gmiSettings.gmi_model}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-800 text-sm mb-3">Deployment Checklist</h3>
            <div className="space-y-2">
              {[
                { label: "Docker Container 8080 Expose", done: true },
                { label: "README Deployment Docs", done: true },
                { label: "Marketplace Listing Draft", done: true },
                { label: "GMI MaaS Credentials", done: gmiSettings?.gmi_maas_configured },
                { label: "AgentBox Publish", done: false },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-2 text-xs">
                  {item.done
                    ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                    : <div className="w-3.5 h-3.5 border-2 border-slate-200 rounded flex-shrink-0" />
                  }
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
    </div>
  );
}
