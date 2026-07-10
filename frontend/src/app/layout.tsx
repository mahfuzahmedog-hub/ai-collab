import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Collaboration Platform",
  description: "Multi-agent AI collaboration workspace",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-950 text-white antialiased">
        {children}
        <Analytics />
      </body>
    </html>
  );
}
