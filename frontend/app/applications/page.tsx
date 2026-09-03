import { Plus, ServerCog } from "lucide-react";

import { getApplications } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ApplicationsPage() {
  const applications = await getApplications();

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 border-b border-console-line pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
            Protected targets
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-normal">Applications</h1>
        </div>
        <button className="inline-flex h-10 items-center gap-2 rounded-lg bg-console-teal px-4 text-sm font-semibold text-black">
          <Plus className="h-4 w-4" aria-hidden />
          Register
        </button>
      </header>

      {applications.length === 0 ? (
        <section className="flex min-h-72 items-center justify-center rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <div className="max-w-sm">
            <ServerCog className="mx-auto h-10 w-10 text-console-muted" aria-hidden />
            <h2 className="mt-4 text-lg font-semibold">No applications registered</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">
              Add the Enterprise Support Agent in the next milestone to begin runtime security and
              red-team evaluation.
            </p>
          </div>
        </section>
      ) : (
        <section className="grid gap-3">
          {applications.map((application) => (
            <article
              key={application.id}
              className="rounded-lg border border-console-line bg-console-panel p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="font-semibold">{application.name}</h2>
                  <p className="mt-1 text-sm text-console-muted">
                    {application.description || "No description"}
                  </p>
                </div>
                <span className="w-fit rounded-full border border-console-green/40 px-3 py-1 text-xs uppercase tracking-[0.16em] text-console-green">
                  {application.status}
                </span>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
