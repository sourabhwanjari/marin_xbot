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
  themeColor: "#ffffff",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="light">
      <body className="antialiased bg-slate-50 text-slate-900 selection:bg-sky-500/20 selection:text-sky-900">
        {children}
      </body>
    </html>
  );
}
