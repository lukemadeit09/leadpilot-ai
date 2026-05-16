import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LeadPilot AI",
  description: "AI-powered CRM automation platform for sales teams."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
