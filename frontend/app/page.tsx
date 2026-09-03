import { Activity, AlertTriangle, Gauge, ShieldCheck } from "lucide-react";

import { StatusCard } from "@/components/status-card";
import { getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const health = await getHealth();

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 border-b border-console-line pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
            Runtime foundation
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-normal text-console-text">
            AegisAI Security Console
          </h1>
        </div>
        <div className="rounded-lg border border-console-line px-3 py-2 text-sm text-console-muted">
          Backend:{" "}
          <span className={health ? "text-console-green" : "text-console-amber"}>
            {health ? health.status : "not connected"}
          </span>
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard
          icon={ShieldCheck}
          label="Security Score"
          value="No run"
          tone="teal"
          detail="Waiting for the evaluation engine"
        />
        <StatusCard
          icon={AlertTriangle}
          label="Critical Findings"
          value="No data"
          tone="red"
          detail="Findings arrive after red-team campaigns"
        />
        <StatusCard
          icon={Activity}
          label="Guardrail Blocks"
          value="No data"
          tone="amber"
          detail="Runtime guardrails arrive in Milestone 2"
        />
        <StatusCard
          icon={Gauge}
          label="P95 Latency"
          value="No data"
          tone="green"
          detail="Metrics arrive with observability"
        />
      </section>

      <section className="rounded-lg border border-console-line bg-console-panel p-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Platform Readiness</h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-console-muted">
              The foundation is wired for authenticated tenant-aware APIs. Security metrics stay
              empty until real evaluators generate them.
            </p>
          </div>
          <div className="hidden rounded-full border border-console-teal/40 px-3 py-1 text-sm text-console-teal sm:block">
            Milestone 1
          </div>
        </div>
      </section>
    </div>
  );
}
