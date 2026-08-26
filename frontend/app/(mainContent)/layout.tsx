"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import LoaderFullscreen from "@/components/LoaderFullscreen";
import { FileSyncNotifier } from "@/components/FileSyncNotifier";
import { WelcomeCelebrationOverlay } from "@/components/WelcomeCelebrationOverlay";
import { useGetMe } from "@/hooks/useUser";
import { canAccessPath, defaultPathForRole } from "@/lib/role-navigation";
import { getAccessToken } from "@/lib/api/session";

export default function ContentLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const router = useRouter();
  const pathname = usePathname();

  // Redirect to login immediately if no token exists — avoids showing a crash
  // screen while the async useGetMe request fires and returns 401.
  const [hasToken] = useState(() => Boolean(getAccessToken()));
  useEffect(() => {
    if (!hasToken) {
      router.replace(`/auth/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [hasToken, pathname, router]);

  const { data: user, isLoading } = useGetMe();
  const isForbidden = Boolean(user && !canAccessPath(user.role, pathname));

  useEffect(() => {
    if (isLoading) {
      return;
    }
    if (!user) {
      router.replace(`/auth/login?redirect=${encodeURIComponent(pathname)}`);
      return;
    }
    if (isForbidden) {
      router.replace(defaultPathForRole(user.role));
    }
  }, [isForbidden, isLoading, pathname, router, user]);

  if (!hasToken || isLoading || !user || isForbidden) {
    return <LoaderFullscreen />;
  }

  return (
    <div className="flex min-h-screen w-full gap-2 bg-white p-2">
      <Sidebar />
      <div className="relative min-h-[calc(100vh-16px)] flex-1 overflow-y-auto">
        {children}
      </div>
      <FileSyncNotifier user={user} />
      <WelcomeCelebrationOverlay user={user} />
    </div>
  );
}
