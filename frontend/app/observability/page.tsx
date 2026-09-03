import { Activity, AlertTriangle, Database, Gauge, ShieldCheck } from "lucide-react";

import { ObservabilityCharts } from "@/components/observability-charts";
import { StatusCard } from "@/components/status-card";
import { getObservabilitySummary } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ObservabilityPage() {
  const summary = await getObservabilitySummary();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Observability
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal text-console-text">
          Runtime Security Signals
        </h1>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard
          icon={ShieldCheck}
          label="Latest Score"
          value={summary.latest_score ? `${summary.latest_score}` : "No run"}
          tone="teal"
          detail="Most recent persisted campaign score"
        />
        <StatusCard
          icon={Activity}
          label="Requests"
          value={`${summary.request_count}`}
          tone="green"
          detail="Support and campaign runtime traces"
        />
        <StatusCard
          icon={AlertTriangle}
          label="Guardrail Blocks"
          value={`${summary.guardrail_blocks}`}
          tone="red"
          detail="Prompt injection blocks recorded"
        />
        <StatusCard
          icon={Gauge}
          label="PII Redactions"
          value={`${summary.pii_redactions}`}
          tone="amber"
          detail="Sanitized model outputs"
        />
      </section>

      <ObservabilityCharts summary={summary} />

      <section className="rounded-lg border border-console-line bg-console-panel p-5">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-console-teal" aria-hidden />
          <div>
            <h2 className="text-lg font-semibold tracking-normal">Prometheus Export</h2>
            <p className="mt-1 text-sm leading-6 text-console-muted">
              Scrape `GET /metrics` on the backend for Sentinel Aegis request, guardrail, campaign,
              and attack-result counters.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
