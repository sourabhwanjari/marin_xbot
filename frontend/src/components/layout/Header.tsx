"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Map, MessageSquare, Info } from "lucide-react";

export interface HeaderProps {
  systemStatus?: string;
  onNewChat?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus = "Operational",
}) => {
  const pathname = usePathname();

  const navLinks = [
    { href: "/", label: "Home", icon: <MessageSquare className="w-3.5 h-3.5" /> },
    { href: "/map", label: "Map", icon: <Map className="w-3.5 h-3.5" /> },
    { href: "/about", label: "About", icon: <Info className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="sticky top-0 z-50 w-full bg-[#070d19]/90 backdrop-blur-md border-b border-slate-800/90 px-4 lg:px-8 py-2.5">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
        {/* Left: MARINEX AI Branding */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 via-sky-600 to-blue-700 flex items-center justify-center text-white shadow-sm shadow-cyan-500/30 group-hover:scale-105 transition-transform">
            <Compass className="w-4 h-4 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base sm:text-lg tracking-tight text-white group-hover:text-cyan-300 transition-colors">
                MARINEX<span className="text-cyan-400">.AI</span>
              </span>
            </div>
            <p className="text-[10px] sm:text-[11px] text-cyan-400/80 font-medium leading-none">
              Marine Intelligence Assistant
            </p>
          </div>
        </Link>

        {/* Center: Minimal Navigation (Home | Map | About) */}
        <nav className="flex items-center space-x-1 sm:space-x-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800/80 shadow-inner">
          {navLinks.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-cyan-950/70 text-cyan-300 border border-cyan-500/40 shadow-xs shadow-cyan-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
                }`}
              >
                <span className={isActive ? "text-cyan-400" : "text-slate-400"}>
                  {link.icon}
                </span>
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right: Operational Status */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium px-2.5 py-1 rounded-lg bg-slate-900/60 border border-slate-800/80">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="hidden sm:inline text-[11px] text-slate-300 font-mono">
              {systemStatus}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
