import { ClipboardList } from "lucide-react";

import { getPolicies } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PoliciesPage() {
  const policies = await getPolicies();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Policy center
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Policies</h1>
      </header>

      {policies.length === 0 ? (
        <section className="flex min-h-72 items-center justify-center rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <div className="max-w-sm">
            <ClipboardList className="mx-auto h-10 w-10 text-console-muted" aria-hidden />
            <h2 className="mt-4 text-lg font-semibold">No policies created</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">
              Policy documents created through the API appear here with their version and status.
            </p>
          </div>
        </section>
      ) : (
        <section className="grid gap-3">
          {policies.map((policy) => {
            const tools = Object.entries(policy.document.tools ?? {});
            return (
              <article key={policy.id} className="rounded-lg border border-console-line bg-console-panel p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="font-semibold">{policy.name}</h2>
                    <p className="mt-1 text-sm text-console-muted">
                      Version {policy.version} · {tools.length} tool rules
                    </p>
                  </div>
                  <span
                    className={
                      policy.status === "active"
                        ? "w-fit rounded-lg border border-console-green/40 px-3 py-1 text-xs uppercase tracking-[0.16em] text-console-green"
                        : "w-fit rounded-lg border border-console-line px-3 py-1 text-xs uppercase tracking-[0.16em] text-console-muted"
                    }
                  >
                    {policy.status}
                  </span>
                </div>
                {tools.length > 0 ? (
                  <div className="mt-4 grid gap-2">
                    {tools.map(([toolName, rule]) => (
                      <div
                        key={toolName}
                        className="grid gap-2 rounded border border-console-line bg-black/20 p-3 text-sm sm:grid-cols-[180px_90px_1fr]"
                      >
                        <span className="font-medium text-console-text">{toolName}</span>
                        <span className="text-console-amber">{rule.risk ?? "MEDIUM"}</span>
                        <span className="text-console-muted">
                          {(rule.allowed_roles ?? []).join(", ") || "No roles"}{" "}
                          {rule.require_approval ? "· approval required" : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : null}
              </article>
            );
          })}
        </section>
      )}
    </div>
  );
}
