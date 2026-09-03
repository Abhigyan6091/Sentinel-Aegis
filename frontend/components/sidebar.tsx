import {
  Activity,
  BarChart3,
  Bug,
  ClipboardList,
  FileWarning,
  Gauge,
  GitBranch,
  Headset,
  LayoutDashboard,
  ListChecks,
  Route,
  Settings,
  Shield,
  UserCheck,
} from "lucide-react";
import Link from "next/link";

const items = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Applications", href: "/applications", icon: Shield },
  { label: "Support Agent", href: "/support", icon: Headset },
  { label: "Attack Campaigns", href: "/campaigns", icon: GitBranch },
  { label: "Attack Explorer", href: "/attacks", icon: Bug },
  { label: "Findings", href: "/findings", icon: FileWarning },
  { label: "Policies", href: "/policies", icon: ClipboardList },
  { label: "Approvals", href: "/approvals", icon: UserCheck },
  { label: "Traces", href: "/traces", icon: Route },
  { label: "Guardrails", href: "/guardrails", icon: ListChecks },
  { label: "Evaluations", href: "/evaluations", icon: BarChart3 },
  { label: "Observability", href: "/observability", icon: Activity },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="border-console-line bg-console-panel/95 md:fixed md:inset-y-0 md:left-0 md:w-64 md:border-r">
      <div className="flex h-full flex-col">
        <div className="border-b border-console-line px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-console-teal/40 bg-console-teal/10">
              <Gauge className="h-5 w-5 text-console-teal" aria-hidden />
            </div>
            <div>
              <p className="text-base font-semibold">Sentinel Aegis</p>
              <p className="text-xs text-console-muted">Security Platform</p>
            </div>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 py-3 md:flex-1 md:flex-col md:overflow-visible">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex h-10 shrink-0 items-center gap-3 rounded-lg px-3 text-sm text-console-muted transition hover:bg-white/5 hover:text-console-text"
            >
              <item.icon className="h-4 w-4" aria-hidden />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
