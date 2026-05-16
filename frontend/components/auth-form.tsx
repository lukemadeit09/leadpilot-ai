"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, setToken } from "@/lib/api";
import { Alert, buttonClass, Field, inputClass } from "@/components/ui";
import type { User } from "@/types";

type AuthResponse = { access_token: string; user: User };

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const payload =
      mode === "register"
        ? { full_name: data.get("full_name"), email: data.get("email"), password: data.get("password") }
        : { email: data.get("email"), password: data.get("password") };
    try {
      const result = await api<AuthResponse>(`/auth/${mode}`, { method: "POST", body: JSON.stringify(payload) });
      setToken(result.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="w-full max-w-md space-y-5 rounded-lg border border-line/80 bg-panel/95 p-6 shadow-glow">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-steel">LeadPilot AI</p>
        <h1 className="mt-2 text-2xl font-semibold text-white">{mode === "login" ? "Sign in" : "Create workspace"}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-400">Access the revenue operations dashboard and AI CRM workflow.</p>
      </div>
      {mode === "register" && (
        <Field label="Full name">
          <input name="full_name" className={inputClass} required minLength={2} />
        </Field>
      )}
      <Field label="Email">
        <input name="email" type="email" className={inputClass} required />
      </Field>
      <Field label="Password">
        <input name="password" type="password" className={inputClass} required minLength={8} />
      </Field>
      {error && <Alert>{error}</Alert>}
      <button className={`${buttonClass} w-full`} disabled={loading}>
        {loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
        <ArrowRight size={16} />
      </button>
      <p className="text-sm text-slate-500">
        {mode === "login" ? "Need an account? " : "Already registered? "}
        <Link className="text-mint" href={mode === "login" ? "/register" : "/login"}>
          {mode === "login" ? "Register" : "Log in"}
        </Link>
      </p>
    </form>
  );
}
