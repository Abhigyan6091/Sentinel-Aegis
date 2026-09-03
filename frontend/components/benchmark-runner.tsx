"use client";

import { BarChart3, Play, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { runBenchmark, type BenchmarkResponse } from "@/lib/api";

function percent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function labelForMode(mode: string) {
  return mode
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function BenchmarkRunner() {
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setLoading(true);
    setError(null);
    try {
      setBenchmark(await runBenchmark());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Benchmark failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-console-line bg-console-panel p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-console-teal" aria-hidden />
              <h2 className="text-lg font-semibold">Defense Mode Benchmark</h2>
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-console-muted">
              Compares no-defense, rules, classifier, LLM-judge, and layered guardrail modes
              against the same deterministic attack set.
            </p>
          </div>
          <button
            onClick={start}
            disabled={loading}
            className="inline-flex h-10 w-fit items-center gap-2 rounded-lg bg-console-teal px-4 text-sm font-semibold text-black disabled:opacity-50"
          >
            <Play className="h-4 w-4" aria-hidden />
            {loading ? "Running" : "Run Benchmark"}
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-console-red">{error}</p> : null}
      </section>

      {benchmark ? (
        <section className="rounded-lg border border-console-line bg-console-panel p-5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-console-green" aria-hidden />
            <h2 className="text-lg font-semibold">{benchmark.name}</h2>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-console-muted">
                <tr>
                  <th className="border-b border-console-line py-2">Mode</th>
                  <th className="border-b border-console-line py-2">Score</th>
                  <th className="border-b border-console-line py-2">Attack Success</th>
                  <th className="border-b border-console-line py-2">Detection Rate</th>
                  <th className="border-b border-console-line py-2">Findings</th>
                </tr>
              </thead>
              <tbody>
                {benchmark.runs.map((run) => (
                  <tr key={run.defense_mode}>
                    <td className="border-b border-console-line py-3 font-medium">
                      {labelForMode(run.defense_mode)}
                    </td>
                    <td className="border-b border-console-line py-3">
                      {run.score.overall}/100
                    </td>
                    <td className="border-b border-console-line py-3">
                      {percent(run.attack_success_rate)}
                    </td>
                    <td className="border-b border-console-line py-3">
                      {percent(run.score.detection_rate)}
                    </td>
                    <td className="border-b border-console-line py-3">
                      {run.findings_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        <section className="rounded-lg border border-dashed border-console-line bg-console-panel p-8 text-center">
          <h2 className="text-lg font-semibold">No benchmark results yet</h2>
          <p className="mt-2 text-sm text-console-muted">
            Run a benchmark to compare layered defenses against weaker runtime modes.
          </p>
        </section>
      )}
    </div>
  );
}
