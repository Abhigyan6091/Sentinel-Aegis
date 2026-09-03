import { FileWarning } from "lucide-react";

import { getFindings } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function FindingsPage() {
  const findings = await getFindings();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Vulnerability management
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Findings</h1>
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
            <article key={finding.finding_id} className="rounded-lg border border-console-line bg-console-panel p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="font-semibold">{finding.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-console-muted">{finding.impact}</p>
                  <p className="mt-2 text-sm leading-6 text-console-muted">
                    {finding.recommendation}
                  </p>
                </div>
                <span className="w-fit rounded-full border border-console-red/40 px-3 py-1 text-xs text-console-red">
                  {finding.severity}
                </span>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
