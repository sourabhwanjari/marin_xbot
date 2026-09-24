import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MARINEX AI — Marine Intelligence & Decision Support",
  description:
    "AI-Powered Marine Intelligence & Decision Support Platform. Built for ORCA: Marine EcOsystem Reasoning with Collaborative Agents.",
  keywords: [
    "Marine Intelligence",
    "Potential Fishing Zones",
    "INCOIS",
    "MOSDAC",
    "Ocean Weather",
    "Geofencing",
    "ORCA",
  ],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#070d19",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#070d19] text-slate-100 selection:bg-cyan-500/20 selection:text-cyan-200 min-h-screen flex flex-col">
        {children}
      </body>
    </html>
  );
}
