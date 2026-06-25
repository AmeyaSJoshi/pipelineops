"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Database, Users, AlertTriangle,
  FileText, MessageSquare, Settings, Zap, BookOpen, Briefcase
} from "lucide-react";

const nav = [
  { href: "/",          label: "Dashboard",  icon: LayoutDashboard },
  { href: "/sources",   label: "Sources",    icon: Database },
  { href: "/roles",     label: "Roles",      icon: Briefcase },
  { href: "/candidates",label: "Candidates", icon: Users },
  { href: "/anomalies", label: "Anomalies",  icon: AlertTriangle },
  { href: "/reports",   label: "Reports",    icon: FileText },
  { href: "/chat",      label: "Chat",       icon: MessageSquare },
  { href: "/settings",  label: "Settings",   icon: Settings },
  { href: "/docs/gmi",  label: "GMI Docs",   icon: BookOpen },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-[200px] flex-shrink-0 flex flex-col h-full bg-[#0f172a] text-slate-300">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-blue-500 rounded-md flex items-center justify-center flex-shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-white font-semibold text-sm leading-tight">PipelineOps</div>
            <div className="text-slate-500 text-[10px] leading-tight">AI Recruiting Agent</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-slate-700/70 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* AgentBox badge */}
      <div className="px-4 py-3 border-t border-slate-700/50">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-slate-400">AgentBox Ready</span>
        </div>
      </div>
    </aside>
  );
}
