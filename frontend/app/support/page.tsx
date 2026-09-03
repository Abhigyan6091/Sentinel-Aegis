import { SupportChat } from "@/components/support-chat";

export default function SupportPage() {
  return (
    <div className="space-y-6">
      <header className="border-b border-console-line pb-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-console-teal">
          Secure demo app
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">Support Agent Runtime</h1>
      </header>
      <SupportChat />
    </div>
  );
}
