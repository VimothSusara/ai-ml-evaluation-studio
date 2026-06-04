"use client";

import { setToken } from "@/lib/auth/token";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, Suspense } from "react";

function CallbackInner() {
  const params = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      setToken(token);
      router.replace("/datasets");
    } else {
      router.replace("/login?error=oauth");
    }
  }, [params, router]);

  return <p className="p-8 text-center">Completing sign in…</p>;
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<p className="p-8 text-center">Loading…</p>}>
      <CallbackInner />
    </Suspense>
  );
}
