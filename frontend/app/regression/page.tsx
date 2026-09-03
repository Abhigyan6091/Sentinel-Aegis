import { FlaskConical } from "lucide-react";

import { getRegressionCases } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RegressionPage() {
  const cases = await getRegressionCases();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Security research workflow
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Regression Suite</h1>
        <p className="mt-2 text-sm leading-6 text-console-muted">
          {cases.length} committed cases. Unlike campaigns, these replay a fixed set and
          must stay green: each one was a real finding before it was mitigated.
        </p>
      </header>

      {cases.length === 0 ? (
        <section className="flex min-h-72 items-center justify-center rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <div className="max-w-sm">
            <FlaskConical className="mx-auto h-10 w-10 text-console-muted" aria-hidden />
            <h2 className="mt-4 text-lg font-semibold">No regression cases</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">
              Promote a finding to turn it into a committed regression case.
            </p>
          </div>
        </section>
      ) : (
        <section className="grid gap-3">
          {cases.map((regressionCase) => (
            <article
              key={regressionCase.case_id}
              className="rounded-lg border border-console-line bg-console-panel p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <h2 className="font-semibold">{regressionCase.title}</h2>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em] text-console-muted">
                    {regressionCase.case_id} · {regressionCase.category}
                  </p>
                  <p className="mt-3 break-words rounded border border-console-line bg-console-bg/40 p-3 font-mono text-xs leading-5 text-console-muted">
                    {regressionCase.payload}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-console-muted">
                    Expected: {regressionCase.expected_behavior}
                  </p>
                </div>
                <span className="w-fit rounded-full border border-console-amber/40 px-3 py-1 text-xs text-console-amber">
                  {regressionCase.severity}
                </span>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
