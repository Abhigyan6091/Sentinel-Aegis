"use client";

import { Play, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { runCampaign, type CampaignRunResponse } from "@/lib/api";

function percent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

export function CampaignRunner({ initial }: { initial: CampaignRunResponse | null }) {
  const [campaign, setCampaign] = useState<CampaignRunResponse | null>(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setLoading(true);
    setError(null);
    try {
      setCampaign(await runCampaign());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Campaign failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-console-line bg-console-panel p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Deterministic Campaign</h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-console-muted">
              Launches controlled attacks through the same Support Agent runtime path used by
              normal traffic.
            </p>
          </div>
          <button
            onClick={start}
            disabled={loading}
            className="inline-flex h-10 w-fit items-center gap-2 rounded-lg bg-console-teal px-4 text-sm font-semibold text-black disabled:opacity-50"
          >
            <Play className="h-4 w-4" aria-hidden />
            {loading ? "Running" : "Start Campaign"}
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-console-red">{error}</p> : null}
      </section>

      {campaign ? (
        <>
          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Security Score" value={`${campaign.score.overall}/100`} />
            <Metric label="Attacks Executed" value={String(campaign.score.attacks_executed)} />
            <Metric label="Attack Success" value={percent(campaign.score.attack_success_rate)} />
            <Metric label="Detection Rate" value={percent(campaign.score.detection_rate)} />
          </section>
          <section className="rounded-lg border border-console-line bg-console-panel p-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-console-teal" aria-hidden />
              <h2 className="text-lg font-semibold">Results</h2>
            </div>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="text-console-muted">
                  <tr>
                    <th className="border-b border-console-line py-2">Attack</th>
                    <th className="border-b border-console-line py-2">Category</th>
                    <th className="border-b border-console-line py-2">Mutation</th>
                    <th className="border-b border-console-line py-2">Outcome</th>
                    <th className="border-b border-console-line py-2">Signals</th>
                  </tr>
                </thead>
                <tbody>
                  {campaign.results.map((result) => (
                    <tr key={result.variant.attack_id}>
                      <td className="border-b border-console-line py-3 font-medium">
                        {result.variant.attack_id}
                      </td>
                      <td className="border-b border-console-line py-3">
                        {result.variant.category}
                      </td>
                      <td className="border-b border-console-line py-3">
                        {result.variant.mutation_strategy}
                      </td>
                      <td className="border-b border-console-line py-3">
                        {result.evaluation.successful_attack ? "BYPASSED" : "BLOCKED"}
                      </td>
                      <td className="border-b border-console-line py-3 text-console-muted">
                        {result.evaluation.detection_signals.slice(0, 2).join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <h2 className="text-lg font-semibold">No campaign results yet</h2>
          <p className="mt-2 text-sm text-console-muted">
            Run the deterministic campaign to generate measured red-team results.
          </p>
        </section>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-console-line bg-console-panel p-4">
      <p className="text-sm text-console-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </article>
  );
}
