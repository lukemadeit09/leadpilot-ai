import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LeadPilot AI | AI CRM Automation",
  description: "AI-powered CRM automation platform that analyzes inbound leads, drafts replies, creates tasks, and grounds sales workflows in company knowledge.",
  openGraph: {
    title: "LeadPilot AI",
    description: "AI-powered CRM automation for B2B sales teams.",
    type: "website"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
