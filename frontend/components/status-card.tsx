import type { LucideIcon } from "lucide-react";

const toneClasses = {
  amber: "border-console-amber/40 text-console-amber",
  green: "border-console-green/40 text-console-green",
  red: "border-console-red/40 text-console-red",
  teal: "border-console-teal/40 text-console-teal",
};

type StatusCardProps = {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
  tone: keyof typeof toneClasses;
};

export function StatusCard({ icon: Icon, label, value, detail, tone }: StatusCardProps) {
  return (
    <article className="rounded-lg border border-console-line bg-console-panel p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-console-muted">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-normal">{value}</p>
        </div>
        <div className={`rounded-lg border p-2 ${toneClasses[tone]}`}>
          <Icon className="h-4 w-4" aria-hidden />
        </div>
      </div>
      <p className="mt-4 text-sm leading-5 text-console-muted">{detail}</p>
    </article>
  );
}
