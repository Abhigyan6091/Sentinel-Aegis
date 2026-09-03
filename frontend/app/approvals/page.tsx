import { CheckCheck } from "lucide-react";

import { getApprovals } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ApprovalsPage() {
  const approvals = await getApprovals();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Approval queue
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Tool Approvals</h1>
      </header>

      {approvals.length === 0 ? (
        <section className="flex min-h-72 items-center justify-center rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <div className="max-w-sm">
            <CheckCheck className="mx-auto h-10 w-10 text-console-muted" aria-hidden />
            <h2 className="mt-4 text-lg font-semibold">No approval requests</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">
              High-risk tool calls create pending approval records before execution.
            </p>
          </div>
        </section>
      ) : (
        <section className="grid gap-3">
          {approvals.map((approval) => (
            <article key={approval.id} className="rounded-lg border border-console-line bg-console-panel p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="font-semibold">{approval.tool_name}</h2>
                  <p className="mt-1 text-sm text-console-muted">{approval.request_id}</p>
                  <p className="mt-3 text-sm leading-6 text-console-muted">
                    {Object.entries(approval.arguments)
                      .map(([key, value]) => `${key}: ${value}`)
                      .join(" · ") || "No arguments captured"}
                  </p>
                  {approval.decision_reason ? (
                    <p className="mt-2 text-sm leading-6 text-console-muted">
                      {approval.decision_reason}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-lg border border-console-amber/40 px-3 py-1 text-xs text-console-amber">
                    {approval.risk}
                  </span>
                  <span className="rounded-lg border border-console-line px-3 py-1 text-xs uppercase tracking-[0.16em] text-console-muted">
                    {approval.status}
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
