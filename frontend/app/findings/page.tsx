import { FileWarning, FlaskConical } from "lucide-react";

import { getFindings, type FindingStatus } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_STYLES: Record<FindingStatus, string> = {
  open: "border-console-red/40 text-console-red",
  triaged: "border-console-amber/40 text-console-amber",
  fixed: "border-console-teal/40 text-console-teal",
  accepted_risk: "border-console-amber/40 text-console-amber",
  closed: "border-console-line text-console-muted",
};

function statusLabel(status: FindingStatus): string {
  return status.replace("_", " ");
}

export default async function FindingsPage() {
  const findings = await getFindings();
  const open = findings.filter((finding) => finding.status === "open").length;

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Vulnerability management
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Findings</h1>
        <p className="mt-2 text-sm leading-6 text-console-muted">
          {findings.length} tracked · {open} awaiting triage. Promote a finding to a
          regression case to lock the mitigation in place.
        </p>
      </header>
      {findings.length === 0 ? (
        <section className="flex min-h-72 items-center justify-center rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <div className="max-w-sm">
            <FileWarning className="mx-auto h-10 w-10 text-console-muted" aria-hidden />
            <h2 className="mt-4 text-lg font-semibold">No open findings</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">
              Findings appear only when a campaign observes a successful attack.
            </p>
          </div>
        </section>
      ) : (
        <section className="grid gap-3">
          {findings.map((finding) => (
            <article
              key={finding.id}
              className="rounded-lg border border-console-line bg-console-panel p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <h2 className="font-semibold">{finding.title}</h2>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em] text-console-muted">
                    {finding.category} · {finding.attack_id ?? "no attack id"}
                  </p>
                  {finding.impact ? (
                    <p className="mt-3 text-sm leading-6 text-console-muted">{finding.impact}</p>
                  ) : null}
                  <p className="mt-2 text-sm leading-6 text-console-muted">
                    {finding.remediation ?? finding.recommendation}
                  </p>
                  {finding.reproduction_steps.length > 0 ? (
                    <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm leading-6 text-console-muted">
                      {finding.reproduction_steps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  ) : null}
                  {finding.regression_case_id ? (
                    <p className="mt-3 flex items-center gap-2 text-sm text-console-teal">
                      <FlaskConical className="h-4 w-4" aria-hidden />
                      <span>Regression case {finding.regression_case_id}</span>
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="w-fit rounded-full border border-console-red/40 px-3 py-1 text-xs text-console-red">
                    {finding.severity}
                  </span>
                  <span
                    className={`w-fit rounded-full border px-3 py-1 text-xs uppercase tracking-[0.16em] ${STATUS_STYLES[finding.status]}`}
                  >
                    {statusLabel(finding.status)}
                  </span>
                </div>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
