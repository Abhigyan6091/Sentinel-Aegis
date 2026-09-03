import { Route } from "lucide-react";

import { getTraces } from "@/lib/api";

export const dynamic = "force-dynamic";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default async function TracesPage() {
  const traces = await getTraces();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Trace explorer
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal text-console-text">
          Runtime Request Traces
        </h1>
      </header>

      {traces.length === 0 ? (
        <section className="rounded-lg border border-console-line bg-console-panel p-5 text-sm text-console-muted">
          Run a support prompt or a red-team campaign to persist trace spans.
        </section>
      ) : (
        <section className="space-y-4">
          {traces.map((trace) => (
            <article key={trace.id} className="rounded-lg border border-console-line bg-console-panel p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="rounded-lg border border-console-teal/40 p-2 text-console-teal">
                    <Route className="h-4 w-4" aria-hidden />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold tracking-normal">{trace.request_id}</h2>
                    <p className="mt-1 text-sm text-console-muted">
                      {trace.application_id ?? "default application"} · {formatDate(trace.created_at)}
                    </p>
                  </div>
                </div>
                <span className="rounded-lg border border-console-line px-3 py-1 text-sm text-console-muted">
                  {trace.spans.length} spans
                </span>
              </div>

              <div className="mt-5 space-y-3">
                {trace.spans.map((span, index) => (
                  <div
                    key={`${trace.id}-${span.component}-${index}`}
                    className="grid gap-3 border-l border-console-line pl-4 sm:grid-cols-[180px_120px_1fr]"
                  >
                    <span className="text-sm font-medium text-console-text">{span.component}</span>
                    <span
                      className={
                        span.decision === "BLOCK" || span.decision === "SANITIZE"
                          ? "text-sm font-medium text-console-amber"
                          : "text-sm font-medium text-console-green"
                      }
                    >
                      {span.decision}
                    </span>
                    <span className="text-sm leading-6 text-console-muted">{span.reason}</span>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
