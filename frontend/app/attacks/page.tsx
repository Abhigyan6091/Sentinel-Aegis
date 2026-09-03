import { getAttackCatalog } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AttacksPage() {
  const attacks = await getAttackCatalog();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Attack explorer
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Attack Catalog</h1>
      </header>
      <section className="grid gap-3">
        {attacks.map((attack) => (
          <article key={attack.seed_id} className="rounded-lg border border-console-line bg-console-panel p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="font-semibold">{attack.category.replaceAll("_", " ")}</h2>
                <p className="mt-2 text-sm leading-6 text-console-muted">{attack.payload}</p>
                <p className="mt-2 text-sm text-console-muted">{attack.expected_behavior}</p>
              </div>
              <span className="w-fit rounded-full border border-console-amber/40 px-3 py-1 text-xs text-console-amber">
                {attack.severity}
              </span>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
