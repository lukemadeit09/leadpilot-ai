"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { buttonClass, secondaryButtonClass } from "@/components/ui";
import { api, getToken } from "@/lib/api";
import type { BillingCheckout, PlanType } from "@/types";

const plans: Array<{ plan: PlanType; name: string; price: string; limit: string; detail: string }> = [
  { plan: "starter", name: "Starter", price: "$5", limit: "$5 AI credits / month", detail: "For demos, solo operators, and early validation." },
  { plan: "pro", name: "Pro", price: "$50", limit: "$50 AI credits / month", detail: "For small sales teams running daily lead analysis." },
  { plan: "agency", name: "Agency", price: "$250", limit: "$250 AI credits / month", detail: "For high-volume teams and client service workflows." }
];

export function PricingClient() {
  const [loadingPlan, setLoadingPlan] = useState<PlanType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(Boolean(getToken()));
  }, []);

  const checkout = async (plan: PlanType) => {
    setError(null);
    setLoadingPlan(plan);
    try {
      const response = await api<BillingCheckout>("/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ plan })
      });
      window.location.href = response.checkout_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start checkout");
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <main className="min-h-screen bg-ink px-6 py-14 text-white">
      <section className="mx-auto max-w-6xl">
        <div className="mb-10 max-w-3xl">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-steel">Pricing</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-normal md:text-6xl">Plans built around AI usage, not seats alone.</h1>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            Pick a monthly AI credit tier for your organization. Stripe handles checkout, subscription updates, and billing portal access.
          </p>
        </div>
        {error && <p className="mb-5 rounded-md border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-100">{error}</p>}
        <div className="grid gap-4 lg:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.plan} className="rounded-lg border border-line/80 bg-panel/95 p-6 shadow-sm shadow-black/20">
              <p className="text-sm font-semibold text-mint">{plan.name}</p>
              <div className="mt-4 flex items-end gap-2">
                <span className="text-4xl font-semibold">{plan.price}</span>
                <span className="pb-1 text-sm text-slate-500">/ month</span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{plan.limit}</p>
              <p className="mt-2 min-h-12 text-sm leading-6 text-slate-500">{plan.detail}</p>
              {isAuthenticated ? (
                <button className={buttonClass} disabled={loadingPlan !== null} onClick={() => checkout(plan.plan)} type="button">
                  {loadingPlan === plan.plan ? "Opening checkout..." : `Choose ${plan.name}`}
                </button>
              ) : (
                <Link className={secondaryButtonClass} href="/register">
                  Create workspace
                </Link>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
