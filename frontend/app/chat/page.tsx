"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Send, Plus, ChevronRight, Zap, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";

const SUGGESTED = [
  { label: "Pipeline Blockers",   text: "Where are candidates dropping off in the funnel?" },
  { label: "Weekly Report",       text: "Summarize the pipeline for my weekly manager update." },
  { label: "Stale Roles",        text: "Which roles haven't had activity in over two weeks?" },
  { label: "Offer Rate",         text: "What's the current offer-to-placement rate?" },
];

type Message = { role: "user" | "assistant"; content: string; ts: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [connectors, setConnectors] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([api.health(), api.connectorSettings(), api.metrics()])
      .then(([h, c, m]) => { setHealth(h); setConnectors(c); setMetrics(m); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text?: string) {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    const userMsg: Message = { role: "user", content: msg, ts: new Date().toLocaleTimeString() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const resp = await api.chat(msg, history);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: resp.response,
        ts: new Date().toLocaleTimeString(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Error connecting to the agent. Make sure the backend is running on port 8080.",
        ts: new Date().toLocaleTimeString(),
      }]);
    }
    setLoading(false);
  }

  const activeConnectors = connectors
    ? Object.entries(connectors as Record<string, { configured: boolean }>)
        .filter(([, v]) => v.configured)
        .map(([k]) => k)
    : [];

  const dbOk = health?.database === "ok";
  const llmOk = health?.gmi_maas_configured;

  return (
    <div className="flex gap-4 h-[calc(100vh-112px)] max-w-5xl">
      {/* Chat area */}
      <div className="flex-1 flex flex-col bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-500">PipelineOps Agent</span>
          {llmOk
            ? <span className="text-[10px] bg-emerald-100 text-emerald-700 font-semibold px-2 py-0.5 rounded-full">GMI MaaS</span>
            : <span className="text-[10px] bg-slate-100 text-slate-500 font-semibold px-2 py-0.5 rounded-full">Demo Fallback</span>}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center text-slate-400 space-y-2">
              <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center">
                <Zap className="w-6 h-6 text-blue-400" />
              </div>
              <p className="text-sm font-medium text-slate-600">PipelineOps Agent</p>
              <p className="text-xs max-w-xs leading-relaxed">
                Ask me about your recruiting pipeline — stale roles, candidate stages, conversion rates,
                or what to tell your manager this week.
              </p>
              {!llmOk && (
                <p className="text-[11px] text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 max-w-xs">
                  Running in template fallback mode. Set GMI_MAAS_BASE_URL + GMI_MAAS_API_KEY for full AI responses.
                </p>
              )}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-slate-900 flex items-center justify-center mr-2 mt-0.5 flex-shrink-0">
                  <Zap className="w-3.5 h-3.5 text-white" />
                </div>
              )}
              <div className="max-w-[75%]">
                <div className={`rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-slate-100 text-slate-800"
                    : "bg-white border border-slate-200 text-slate-800"
                }`}>
                  {m.content}
                </div>
                <div className="text-[10px] text-slate-400 mt-1 px-1">{m.ts}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="w-7 h-7 rounded-full bg-slate-900 flex items-center justify-center mr-2 flex-shrink-0">
                <Zap className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="bg-white border border-slate-200 rounded-xl px-4 py-3">
                <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="p-3 border-t border-slate-100">
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendMessage())}
              placeholder="Ask PipelineOps Agent…"
              className="flex-1 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 outline-none"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="w-8 h-8 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-lg flex items-center justify-center transition-colors"
            >
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
          <p className="text-[10px] text-slate-400 text-center mt-2">
            Agent responses use pipeline data only. Verify critical decisions independently.
          </p>
        </div>
      </div>

      {/* Right sidebar */}
      <div className="w-64 flex-shrink-0 space-y-3">
        {/* System status */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="text-xs font-semibold text-slate-700 mb-3">System Status</h3>
          <div className="space-y-2">
            {[
              { label: "Backend API", ok: dbOk },
              { label: "Database", ok: dbOk },
              { label: "AI / LLM", ok: llmOk },
            ].map(({ label, ok }) => (
              <div key={label} className="flex items-center gap-2">
                {ok
                  ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                  : <AlertCircle className="w-3.5 h-3.5 text-amber-400" />}
                <span className="text-xs text-slate-600">{label}</span>
                <span className={`ml-auto text-[10px] font-semibold ${ok ? "text-emerald-600" : "text-amber-500"}`}>
                  {ok ? "OK" : "—"}
                </span>
              </div>
            ))}
          </div>
          {metrics && (
            <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
              <div className="flex justify-between"><span>Open roles</span><span className="font-semibold text-slate-700">{metrics.open_roles ?? "—"}</span></div>
              <div className="flex justify-between"><span>Active candidates</span><span className="font-semibold text-slate-700">{metrics.active_candidates ?? "—"}</span></div>
              <div className="flex justify-between"><span>Open anomalies</span><span className="font-semibold text-slate-700">{metrics.anomaly_count ?? "—"}</span></div>
            </div>
          )}
        </div>

        {/* Connected data sources — real, not hardcoded */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="text-xs font-semibold text-slate-700 mb-3">Data Sources Available</h3>
          {activeConnectors.length > 0 ? (
            <div className="space-y-1.5">
              {activeConnectors.map(name => (
                <div key={name} className="flex items-center gap-2 bg-emerald-50 border border-emerald-100 px-2 py-1.5 rounded-md">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span className="text-xs text-emerald-800 capitalize">{name.replace("_", " ")}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-slate-400 space-y-1">
              <p>No live connectors configured.</p>
              <p>The agent answers from the seeded demo dataset.</p>
              <a href="/sources" className="text-blue-600 underline">Connect a source →</a>
            </div>
          )}
          <div className="mt-2 flex items-center gap-1.5 text-[10px] text-slate-400">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            Demo data always available
          </div>
        </div>

        {/* Suggested queries */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="text-xs font-semibold text-slate-700 mb-3">Suggested Queries</h3>
          <div className="space-y-1.5">
            {SUGGESTED.map(s => (
              <button
                key={s.label}
                onClick={() => sendMessage(s.text)}
                className="w-full flex items-center justify-between text-left text-xs text-slate-600 hover:bg-slate-50 px-2 py-2 rounded-lg transition-colors group"
              >
                <span className="font-medium">{s.label}</span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
