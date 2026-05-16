import { ArrowRight, Check } from "lucide-react";
import Link from "next/link";

const plans = [
  {
    name: "Starter",
    price: "$0 demo",
    description: "For portfolio demos and solo validation.",
    features: ["AI lead analyzer", "CRM dashboard", "Knowledge base uploads", "Demo-friendly usage limits"]
  },
  {
    name: "Pro",
    price: "$49/mo",
    description: "For small sales teams operationalizing inbound leads.",
    featured: true,
    features: ["Higher AI usage limits", "Async AI worker jobs", "Team CRM workflow", "Priority follow-up queue"]
  },
  {
    name: "Agency",
    price: "$249/mo",
    description: "For high-volume teams and client-facing operators.",
    features: ["Expanded AI quota", "Multi-client sales workflows", "Advanced integrations roadmap", "Deployment support checklist"]
  }
];

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-ink px-6 py-14 text-white">
      <section className="mx-auto max-w-6xl">
        <Link href="/" className="text-sm text-slate-400 hover:text-white">Back to home</Link>
        <div className="mt-10 max-w-3xl">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-steel">Pricing preview</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-0.03em] md:text-6xl">Usage-aware plans for AI revenue operations.</h1>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            LeadPilot AI is built around AI cost controls, monthly usage limits, and upgrade paths. Stripe billing is planned separately; this page gives demo-ready packaging and product positioning.
          </p>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.name} className={`rounded-2xl border p-6 shadow-sm shadow-black/20 ${plan.featured ? "border-mint/40 bg-mint/10" : "border-line/80 bg-panel/95"}`}>
              {plan.featured && <div className="mb-4 inline-flex rounded-full border border-mint/30 bg-mint/15 px-3 py-1 text-xs font-semibold text-mint">Most demo-ready</div>}
              <h2 className="text-xl font-semibold">{plan.name}</h2>
              <p className="mt-3 text-4xl font-semibold">{plan.price}</p>
              <p className="mt-3 min-h-12 text-sm leading-6 text-slate-400">{plan.description}</p>
              <ul className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex gap-3 text-sm text-slate-300">
                    <Check className="mt-0.5 shrink-0 text-mint" size={16} />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link href="/register" className={`mt-7 inline-flex w-full items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold ${plan.featured ? "bg-mint text-ink" : "border border-line bg-white/[0.03] text-slate-100"}`}>
                Start with {plan.name} <ArrowRight size={16} />
              </Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
