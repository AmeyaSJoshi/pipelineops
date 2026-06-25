"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Upload, Sheet, Building2, Users2, Briefcase, Globe,
  CheckCircle2, AlertCircle, Clock, Zap, ExternalLink, RefreshCw
} from "lucide-react";

const SOURCE_META: Record<string, { icon: any; label: string; color: string }> = {
  csv:          { icon: Upload,    label: "CSV Upload",     color: "text-blue-600" },
  google_sheets:{ icon: Sheet,     label: "Google Sheets",  color: "text-green-600" },
  greenhouse:   { icon: Building2, label: "Greenhouse",     color: "text-emerald-600" },
  lever:        { icon: Users2,    label: "Lever",          color: "text-orange-500" },
  bullhorn:     { icon: Briefcase, label: "Bullhorn",       color: "text-purple-600" },
  indeed:       { icon: Globe,     label: "Indeed",         color: "text-blue-500" },
  careerbuilder:{ icon: Globe,     label: "CareerBuilder",  color: "text-red-500" },
  monster:      { icon: Globe,     label: "Monster",        color: "text-violet-500" },
  dice:         { icon: Globe,     label: "Dice",           color: "text-cyan-600" },
};

function StatusBadge({ status }: { status: string }) {
  if (status === "connected") return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">● Connected</span>;
  if (status === "demo") return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Demo Mode</span>;
  if (status === "needs_credentials") return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">Coming Soon</span>;
  return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">{status}</span>;
}

export default function Sources() {
  const [sources, setSources] = useState<any[]>([]);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.sources().then(d => { setSources(d.sources || []); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  async function runDemoSync(sourceType: string) {
    setSyncing(sourceType);
    try {
      await api.syncDemo(sourceType);
      const d = await api.sources();
      setSources(d.sources || []);
    } catch {}
    setSyncing(null);
  }

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage ingestion endpoints and monitor synchronization health for the PipelineOps recruiting agent.</p>
        </div>
        <button className="flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-2 rounded-lg font-medium transition-colors">
          + Connect New Source
        </button>
      </div>

      {/* GMI Cloud Ready banner */}
      <div className="bg-slate-900 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-500 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-white font-semibold text-sm">GMI Cloud Ready</span>
              <span className="text-[10px] bg-blue-500/30 text-blue-300 px-2 py-0.5 rounded-full font-semibold">BETA</span>
            </div>
            <p className="text-slate-400 text-xs mt-0.5">PipelineOps Agent is fully verified for deployment on GMI Cloud infrastructure. Currently running in isolated mode for demonstration.</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-300 font-mono">Local_Demo_Mode</span>
        </div>
      </div>

      {/* Source cards grid */}
      <div className="grid grid-cols-3 gap-4">
        {sources.map((src: any) => {
          const meta = SOURCE_META[src.source_type] || { icon: Globe, label: src.display_name, color: "text-slate-500" };
          const Icon = meta.icon;
          const isDemo = src.status === "demo";
          const isConnected = src.status === "connected";
          const isSyncing = syncing === src.source_type;
          return (
            <div key={src.id} className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center">
                    <Icon className={`w-4 h-4 ${meta.color}`} />
                  </div>
                  <span className="font-semibold text-sm text-slate-800">{src.display_name}</span>
                </div>
                <StatusBadge status={src.status} />
              </div>

              <div className="space-y-1.5 text-xs text-slate-500">
                <div className="flex justify-between">
                  <span>Last Sync</span>
                  <span className="text-slate-700 font-medium">
                    {src.last_sync_at ? new Date(src.last_sync_at).toLocaleDateString() : "Never"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Records Imported</span>
                  <span className="text-slate-700 font-medium">{src.records_total.toLocaleString()}</span>
                </div>
              </div>

              <div className="pt-1 border-t border-slate-100">
                {isConnected && (
                  <button className="w-full text-xs text-slate-600 border border-slate-200 rounded-md py-1.5 hover:bg-slate-50">
                    Settings
                  </button>
                )}
                {isDemo && (
                  <button
                    onClick={() => runDemoSync(src.source_type)}
                    disabled={isSyncing}
                    className="w-full text-xs text-blue-600 border border-blue-200 bg-blue-50 hover:bg-blue-100 rounded-md py-1.5 flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <RefreshCw className={`w-3 h-3 ${isSyncing ? "animate-spin" : ""}`} />
                    {isSyncing ? "Syncing…" : "Run Demo Sync"}
                  </button>
                )}
                {src.status === "needs_credentials" && (
                  <button className="w-full text-xs text-slate-400 border border-slate-200 rounded-md py-1.5 cursor-not-allowed">
                    Request Beta Access
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {!loading && sources.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <p className="text-sm">No sources found. Run <code className="bg-slate-100 px-1 rounded">/demo/seed</code> to populate.</p>
        </div>
      )}
    </div>
  );
}
