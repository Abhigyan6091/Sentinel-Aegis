import { CampaignRunner } from "@/components/campaign-runner";
import { getLatestCampaign } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CampaignsPage() {
  const latest = await getLatestCampaign();

  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Red-team evaluation
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Attack Campaigns</h1>
      </header>
      <CampaignRunner initial={latest} />
    </div>
  );
}
