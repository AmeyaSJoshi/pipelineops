"use client";
import { useState } from "react";
import { Bell, Info, Search, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import JobProgress from "./JobProgress";

export default function Topbar() {
  const [running,  setRunning]  = useState(false);
  const [progress, setProgress] = useState(0);

  async function runRefresh() {
    setRunning(true);
    setProgress(0);
    try {
      const job = await api.runJob("full_pipeline_refresh");

      const poll = setInterval(async () => {
        try {
          const status = await api.getJob(job.job_id);
          if (typeof status.progress === "number") {
            setProgress(status.progress);
          }
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(poll);
            setProgress(1);
            setTimeout(() => {
              setRunning(false);
              setProgress(0);
              window.dispatchEvent(new Event("pipeline-refreshed"));
            }, 800);
          }
        } catch {
          clearInterval(poll);
          setRunning(false);
        }
      }, 1200);
    } catch {
      setRunning(false);
    }
  }

  return (
    <>
      <header className="h-12 flex items-center gap-3 px-5 bg-white border-b border-slate-200 flex-shrink-0">
        <span className="font-semibold text-slate-800 text-sm mr-1">PipelineOps Agent</span>

        <div className="flex items-center gap-2 flex-1 max-w-xs bg-slate-50 border border-slate-200 rounded-md px-3 py-1.5">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            className="bg-transparent text-xs text-slate-600 placeholder:text-slate-400 outline-none flex-1"
            placeholder="Search pipelines, candidates..."
          />
        </div>

        <div className="flex-1" />

        <a
          href="http://localhost:8080/exports/download"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-600 border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 rounded-md transition-colors"
        >
          Export CSV
        </a>

        <button
          onClick={runRefresh}
          disabled={running}
          className="flex items-center gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-70 text-white px-3 py-1.5 rounded-md transition-colors font-medium"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${running ? "animate-spin" : ""}`} />
          {running ? "Running…" : "Run Full Pipeline Refresh"}
        </button>

        <button className="p-1.5 text-slate-500 hover:text-slate-700 relative">
          <Bell className="w-4 h-4" />
        </button>
        <button className="p-1.5 text-slate-500 hover:text-slate-700">
          <Info className="w-4 h-4" />
        </button>
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-semibold">
          R
        </div>
      </header>

      <JobProgress progress={progress} visible={running} />
    </>
  );
}
