"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Send, Mic, Plus, ChevronRight, Zap, RefreshCw } from "lucide-react";

const SUGGESTED = [
  { label: "Pipeline Blockers", text: "Where are candidates dropping off?" },
  { label: "Reporting", text: "Update my weekly report." },
  { label: "Candidate Sourcing", text: "Find passive leads for frontend engineer." },
];

type Message = { role: "user" | "assistant"; content: string; ts: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
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
      setMessages(prev => [...prev, { role: "assistant", content: resp.response, ts: new Date().toLocaleTimeString() }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Error connecting to the agent. Make sure the backend is running.", ts: new Date().toLocaleTimeString() }]);
    }
    setLoading(false);
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-112px)] max-w-5xl">
      {/* Chat area */}
      <div className="flex-1 flex flex-col bg-white rounded-xl border border-slate-200 overflow-hidden">
        {/* Chat header */}
        <div className="px-4 py-3 border-b border-slate-100 text-xs text-slate-500">Today</div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center text-slate-400 space-y-2">
              <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center">
                <Zap className="w-6 h-6 text-blue-400" />
              </div>
              <p className="text-sm font-medium text-slate-600">PipelineOps Agent</p>
              <p className="text-xs max-w-xs">Ask me about your recruiting pipeline — stale roles, candidate stages, conversion rates, or what to tell your manager this week.</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-slate-900 flex items-center justify-center mr-2 mt-0.5 flex-shrink-0">
                  <Zap className="w-3.5 h-3.5 text-white" />
                </div>
              )}
              <div className={`max-w-[75%] ${m.role === "user" ? "" : ""}`}>
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

        {/* Input */}
        <div className="p-3 border-t border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <button className="flex items-center gap-1 text-[11px] bg-slate-100 hover:bg-slate-200 px-2.5 py-1 rounded-full text-slate-600 transition-colors">
              <Plus className="w-3 h-3" /> All Pipelines
            </button>
          </div>
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendMessage())}
              placeholder="Ask PipelineOps Agent…"
              className="flex-1 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 outline-none"
            />
            <button className="p-1.5 text-slate-400 hover:text-slate-600"><Mic className="w-4 h-4" /></button>
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="w-8 h-8 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-lg flex items-center justify-center transition-colors"
            >
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
          <p className="text-[10px] text-slate-400 text-center mt-2">Agent responses may be inaccurate. Verify critical pipeline decisions.</p>
        </div>
      </div>

      {/* Right sidebar */}
      <div className="w-64 flex-shrink-0 space-y-3">
        {/* System Status */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="text-xs font-semibold text-slate-700 mb-3">System Status</h3>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-600 font-medium">Active & Monitoring</span>
          </div>
          <p className="text-[11px] text-slate-400">Agent has real-time access to ATS database and last synced 4 minutes ago.</p>
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

        {/* Workspace context */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="text-xs font-semibold text-slate-700 mb-3">Current Workspace Context</h3>
          <div className="space-y-1.5 text-[11px] text-slate-500">
            {["Workday", "Greenhouse", "LinkedIn Recruiter"].map(t => (
              <div key={t} className="flex items-center gap-2 bg-slate-50 px-2 py-1.5 rounded-md">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                {t}
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-600 font-medium">⚡ Pipeline Health</span>
              <span className="text-[11px] text-emerald-600 font-bold">
                {health ? (health.database === "ok" ? "92/100" : "—") : "—"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
