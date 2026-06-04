"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken, isAuthenticated } from "@/lib/auth/token";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

const links = [
  { href: "/datasets", label: "Datasets" },
  { href: "/experiments", label: "Experiments" },
  { href: "/jobs", label: "Jobs" },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <p className="text-sm text-zinc-500">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <span className="font-semibold">AI Evaluation Studio</span>
            <nav className="flex gap-4 text-sm">
              {links.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className={
                    pathname.startsWith(l.href)
                      ? "font-medium text-zinc-900"
                      : "text-zinc-500"
                  }
                >
                  {l.label}
                </Link>
              ))}
            </nav>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            Logout
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
