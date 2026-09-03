import { BenchmarkRunner } from "@/components/benchmark-runner";

export const dynamic = "force-dynamic";

export default function EvaluationsPage() {
  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Benchmarking
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Evaluations</h1>
      </header>
      <BenchmarkRunner />
    </div>
  );
}
