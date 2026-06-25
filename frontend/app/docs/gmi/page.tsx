"use client";
import { CheckCircle, Circle, ExternalLink, Zap, Server, Shield, Globe } from "lucide-react";

const CHECKLIST = [
  { group: "Before Deployment", items: [
    { label: "Join GMI Cloud Discord for credits & support", done: false, link: "https://discord.gg/mbYhCJSbF6" },
    { label: "Request hackathon cloud credits", done: false },
    { label: "Create / access GMI Cloud account", done: false },
    { label: "Confirm AgentBox marketplace access", done: false },
  ]},
  { group: "Configuration", items: [
    { label: "Set GMI_MAAS_BASE_URL in environment", done: false },
    { label: "Set GMI_MAAS_API_KEY in environment", done: false },
    { label: "Select GMI MaaS model (GMI_SELECTED_MODEL)", done: false },
    { label: "Verify /health returns gmi_maas_configured: true", done: false },
  ]},
  { group: "Deployment", items: [
    { label: "Docker container built successfully", done: true },
    { label: "Backend exposes port 8080", done: true },
    { label: "POST /run full_pipeline_refresh tested", done: true },
    { label: "GET /jobs/{job_id} polling tested", done: true },
    { label: "Reports and export flow verified", done: true },
  ]},
  { group: "Marketplace Listing", items: [
    { label: "Marketplace listing draft written", done: true },
    { label: "Deploy Docker container to AgentBox", done: false },
    { label: "Publish marketplace listing", done: false },
  ]},
];

const ASYNC_STEPS = [
  { method: "POST", path: "/run", desc: 'Body: { "task": "full_pipeline_refresh" }', response: '202 → { "job_id": "abc123", "status": "pending" }' },
  { method: "GET",  path: "/jobs/abc123", desc: "Poll until status = completed", response: '{ "status": "running", "progress": 0.4 }' },
  { method: "GET",  path: "/jobs/abc123", desc: "Final result", response: '{ "status": "completed", "result": { "metrics": {...} } }' },
];

export default function GMIDocsPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">GMI AgentBox Deployment</h1>
        <p className="text-sm text-slate-500 mt-0.5">Checklist and reference for deploying PipelineOps Agent on GMI Cloud infrastructure.</p>
      </div>

      {/* Status banner */}
      <div className="bg-slate-900 rounded-xl p-5 flex items-start gap-4">
        <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-white font-semibold">PipelineOps Agent — AgentBox Ready</span>
            <span className="text-[10px] bg-amber-500/30 text-amber-300 px-2 py-0.5 rounded-full font-semibold">PENDING CREDENTIALS</span>
          </div>
          <p className="text-slate-400 text-sm leading-relaxed">
            The agent is fully built and locally verified. Deployment to GMI AgentBox requires GMI Cloud credentials.
            Join the Discord at <a href="https://discord.gg/mbYhCJSbF6" target="_blank" rel="noreferrer" className="text-blue-400 underline">discord.gg/mbYhCJSbF6</a> to get hackathon credits.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_300px] gap-5">
        {/* Deployment checklist */}
        <div className="space-y-4">
          {CHECKLIST.map(group => (
            <div key={group.group} className="bg-white rounded-xl border border-slate-200 p-5">
              <h2 className="font-semibold text-slate-800 text-sm mb-3">{group.group}</h2>
              <div className="space-y-2.5">
                {group.items.map((item, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    {item.done
                      ? <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                      : <Circle className="w-4 h-4 text-slate-300 flex-shrink-0 mt-0.5" />
                    }
                    <div className="flex items-center gap-1.5 flex-1">
                      <span className={`text-sm ${item.done ? "text-slate-700" : "text-slate-400"}`}>{item.label}</span>
                      {item.link && (
                        <a href={item.link} target="_blank" rel="noreferrer">
                          <ExternalLink className="w-3 h-3 text-blue-400 hover:text-blue-600" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Right panel */}
        <div className="space-y-4">
          {/* Async job pattern */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Server className="w-4 h-4 text-slate-500" />
              <h3 className="font-semibold text-slate-800 text-sm">AgentBox Async Pattern</h3>
            </div>
            <div className="space-y-3">
              {ASYNC_STEPS.map((step, i) => (
                <div key={i} className="text-[11px] space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${step.method === "POST" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>{step.method}</span>
                    <code className="font-mono text-slate-700">{step.path}</code>
                  </div>
                  <div className="text-slate-500 pl-1">{step.desc}</div>
                  <code className="block bg-slate-50 border border-slate-100 rounded px-2 py-1.5 text-slate-600 text-[10px] leading-relaxed">{step.response}</code>
                </div>
              ))}
            </div>
          </div>

          {/* Environment variables */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-slate-500" />
              <h3 className="font-semibold text-slate-800 text-sm">Required Env Vars</h3>
            </div>
            <div className="space-y-2 font-mono text-[11px]">
              {[
                { key: "GMI_MAAS_BASE_URL", note: "MaaS endpoint" },
                { key: "GMI_MAAS_API_KEY",  note: "API key" },
                { key: "GMI_SELECTED_MODEL",note: "Model ID" },
                { key: "DATABASE_URL",       note: "Postgres in prod" },
                { key: "ALLOW_WRITES",       note: "Set true to enable mutations" },
              ].map(v => (
                <div key={v.key} className="flex justify-between items-start">
                  <code className="text-slate-700 bg-slate-50 px-1.5 py-0.5 rounded">{v.key}</code>
                  <span className="text-slate-400 text-right ml-2">{v.note}</span>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">Never commit secrets. Use AgentBox environment injection or a .env file excluded from version control.</p>
          </div>

          {/* Marketplace */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Globe className="w-4 h-4 text-slate-500" />
              <h3 className="font-semibold text-slate-800 text-sm">Marketplace Category</h3>
            </div>
            <div className="space-y-1.5 text-xs text-slate-600">
              <div className="flex justify-between"><span>Category</span><span className="font-medium">Data & Analytics</span></div>
              <div className="flex justify-between"><span>Status</span><span className="text-amber-600 font-medium">Draft</span></div>
              <div className="flex justify-between"><span>Port</span><span className="font-mono font-medium">8080</span></div>
              <div className="flex justify-between"><span>Health check</span><span className="font-mono font-medium">GET /health</span></div>
            </div>
          </div>

          <a
            href="https://discord.gg/mbYhCJSbF6"
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl p-4 transition-colors group"
          >
            <div>
              <div className="text-sm font-semibold">Join GMI Discord</div>
              <div className="text-xs text-indigo-300 mt-0.5">Get credits & deploy support</div>
            </div>
            <ExternalLink className="w-4 h-4 text-indigo-300 group-hover:text-white transition-colors" />
          </a>
        </div>
      </div>
    </div>
  );
}
