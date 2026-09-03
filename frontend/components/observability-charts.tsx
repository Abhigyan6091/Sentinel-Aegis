import type { ObservabilitySummary } from "@/lib/api";

type ObservabilityChartsProps = {
  summary: ObservabilitySummary;
};

const chartRows = [
  { key: "request_count", label: "Requests", color: "bg-console-teal" },
  { key: "security_events", label: "Security events", color: "bg-console-amber" },
  { key: "attack_results", label: "Attack results", color: "bg-console-green" },
  { key: "findings", label: "Findings", color: "bg-console-red" },
] as const;

const signalRows = [
  { key: "guardrail_blocks", label: "Prompt blocks", color: "bg-console-red" },
  { key: "pii_redactions", label: "PII redactions", color: "bg-console-amber" },
  { key: "campaigns", label: "Campaign runs", color: "bg-console-teal" },
] as const;

function widthFor(value: number, max: number) {
  if (max <= 0 || value <= 0) {
    return "0%";
  }
  return `${Math.max(8, Math.round((value / max) * 100))}%`;
}

export function ObservabilityCharts({ summary }: ObservabilityChartsProps) {
  const maxVolume = Math.max(...chartRows.map((row) => summary[row.key]), 1);
  const maxSignals = Math.max(...signalRows.map((row) => summary[row.key]), 1);

  return (
    <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
      <section className="rounded-lg border border-console-line bg-console-panel p-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold tracking-normal">Runtime Volume</h2>
            <p className="mt-1 text-sm text-console-muted">Tenant-scoped records persisted by the API.</p>
          </div>
          <span className="rounded-lg border border-console-line px-3 py-1 text-sm text-console-muted">
            {summary.request_count} requests
          </span>
        </div>
        <div className="mt-5 space-y-4">
          {chartRows.map((row) => (
            <div key={row.key} className="space-y-2">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="text-console-muted">{row.label}</span>
                <span className="font-medium text-console-text">{summary[row.key]}</span>
              </div>
              <div className="h-3 overflow-hidden rounded bg-black/30">
                <div
                  className={`h-full rounded ${row.color}`}
                  style={{ width: widthFor(summary[row.key], maxVolume) }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-console-line bg-console-panel p-5">
        <h2 className="text-lg font-semibold tracking-normal">Control Signals</h2>
        <div className="mt-5 space-y-4">
          {signalRows.map((row) => (
            <div key={row.key} className="space-y-2">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="text-console-muted">{row.label}</span>
                <span className="font-medium text-console-text">{summary[row.key]}</span>
              </div>
              <div className="h-3 overflow-hidden rounded bg-black/30">
                <div
                  className={`h-full rounded ${row.color}`}
                  style={{ width: widthFor(summary[row.key], maxSignals) }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
