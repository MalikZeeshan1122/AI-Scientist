"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Atom,
  BookOpen,
  FlaskConical,
  KeyRound,
  LayoutDashboard,
  Lightbulb,
  type LucideIcon,
} from "lucide-react";
import { BackendStatus } from "./BackendStatus";
import { SidebarApiKeys } from "./SidebarApiKeys";
import { ThemeToggle } from "./ThemeToggle";
import { cn } from "@/lib/cn";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  badge?: string;
};

const NAV: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/papers", label: "Papers", icon: BookOpen },
  { href: "/ideas", label: "Ideas", icon: Lightbulb },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/drafts", label: "Drafts", icon: Atom },
];

const FOOTER_NAV: NavItem[] = [
  { href: "/settings", label: "API keys", icon: KeyRound },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-ink-700 bg-[var(--bg-sidebar)] px-4 py-5 sticky top-0 h-screen">
      <Link href="/" className="block px-2 mb-8 group">
        <div className="flex items-center gap-2.5">
          <div className="relative h-9 w-9 rounded-xl bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-400 grid place-items-center">
            <Atom className="h-5 w-5 text-white" strokeWidth={2.2} />
            <span className="absolute inset-0 rounded-xl ring-1 ring-black/10" />
          </div>
          <div>
            <div className="text-[15px] font-semibold tracking-tight text-ink-50 leading-none">
              AI Scientist
            </div>
            <div className="text-[10.5px] text-ink-400 mt-1 tracking-wider uppercase">
              autonomous research
            </div>
          </div>
        </div>
      </Link>

      <div className="text-[10px] uppercase tracking-[0.18em] text-ink-500 font-semibold px-3 mb-2">
        Workspace
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition-colors duration-150",
                active
                  ? "text-white bg-orange-500 border border-orange-500 font-semibold"
                  : "text-ink-200 hover:text-ink-50 hover:bg-ink-800 border border-transparent font-medium"
              )}
            >
              <Icon
                className={cn(
                  "h-[15px] w-[15px] transition-colors shrink-0",
                  active
                    ? "text-white"
                    : "text-ink-400 group-hover:text-ink-200"
                )}
                strokeWidth={2}
              />
              <span className="flex-1 tracking-tight">
                {item.label}
              </span>
              {item.badge && (
                <span className="text-[10px] text-orange-600 bg-orange-500/10 border border-orange-500/25 rounded-full px-1.5 py-0.5">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-4 space-y-3">
        <SidebarApiKeys />
        <nav className="flex flex-col gap-1">
          {FOOTER_NAV.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition-colors duration-150",
                  active
                    ? "text-white bg-orange-500 border border-orange-500 font-semibold"
                    : "text-ink-200 hover:text-ink-50 hover:bg-ink-800 border border-transparent font-medium"
                )}
              >
                <Icon
                  className={cn(
                    "h-[15px] w-[15px] shrink-0 transition-colors",
                    active
                      ? "text-white"
                      : "text-ink-400 group-hover:text-ink-200"
                  )}
                  strokeWidth={2}
                />
                <span className="flex-1 tracking-tight">{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <ThemeToggle />
        <BackendStatus />
        <div className="text-[10px] text-ink-500 text-center">
          v0.1.0 · Open source
        </div>
      </div>
    </aside>
  );
}

export function MobileTopBar() {
  return (
    <div className="lg:hidden sticky top-0 z-40 border-b border-ink-700 bg-[var(--bg-sidebar)] px-4 py-3 flex items-center justify-between shadow-sm">
      <Link href="/" className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-400 grid place-items-center">
          <Atom className="h-4 w-4 text-white" strokeWidth={2.2} />
        </div>
        <div className="text-sm font-semibold tracking-tight text-ink-50">
          AI Scientist
        </div>
      </Link>
      <MobileNav />
    </div>
  );
}


function MobileNav() {
  const pathname = usePathname();
  const items = [...NAV, ...FOOTER_NAV];
  return (
    <nav className="flex items-center gap-1 overflow-x-auto">
      {items.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname === item.href || pathname.startsWith(item.href + "/");
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "shrink-0 grid place-items-center h-9 w-9 rounded-lg transition",
              active
                ? "text-white bg-orange-500 border border-orange-600"
                : "text-ink-400 hover:text-ink-50 hover:bg-ink-800"
            )}
            aria-label={item.label}
          >
            <Icon className="h-4 w-4" />
          </Link>
        );
      })}
    </nav>
  );
}
