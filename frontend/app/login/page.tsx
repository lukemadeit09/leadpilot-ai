import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-ink px-4">
      <AuthForm mode="login" />
    </main>
  );
}
