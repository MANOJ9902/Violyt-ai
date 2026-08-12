"use client";

import { useEffect, useMemo } from "react";
import { ArrowLeft } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

const ROUTE_HISTORY_KEY = "violyt.app_route_history";
const MAX_HISTORY_ITEMS = 50;

function readRouteHistory() {
    if (typeof window === "undefined") {
        return [];
    }

    try {
        const parsed = JSON.parse(window.sessionStorage.getItem(ROUTE_HISTORY_KEY) || "[]");
        return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
    } catch {
        return [];
    }
}

function writeRouteHistory(history: string[]) {
    if (typeof window === "undefined") {
        return;
    }
    window.sessionStorage.setItem(ROUTE_HISTORY_KEY, JSON.stringify(history.slice(-MAX_HISTORY_ITEMS)));
}

function fallbackRouteFor(pathname: string) {
    if (pathname === "/dashboard") {
        return "/dashboard";
    }
    if (pathname === "/brand_space" || pathname === "/tenants" || pathname === "/user_management" || pathname === "/analytics" || pathname === "/profile") {
        return "/dashboard";
    }
    if (pathname === "/brand_space/new" || pathname === "/brand_space/usage") {
        return "/brand_space";
    }
    if (pathname.startsWith("/brand_space/")) {
        return "/brand_space";
    }
    if (pathname === "/user_management/create" || pathname.startsWith("/user_management/")) {
        return "/user_management";
    }
    if (pathname === "/tenants/create") {
        return "/tenants";
    }
    const tenantEditMatch = pathname.match(/^\/tenants\/([^/]+)\/edit$/);
    if (tenantEditMatch) {
        return `/tenants/${tenantEditMatch[1]}`;
    }
    if (pathname.startsWith("/tenants/")) {
        return "/tenants";
    }
    return "/dashboard";
}

function shouldShowBackButton(pathname: string) {
    return ![
        "/dashboard",
        "/brand_space",
        "/tenants",
        "/user_management",
        "/analytics",
        "/profile",
    ].includes(pathname);
}

export function AppBackButton() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const currentRoute = useMemo(() => {
        const query = searchParams.toString();
        return query ? `${pathname}?${query}` : pathname;
    }, [pathname, searchParams]);

    useEffect(() => {
        const history = readRouteHistory();
        const existingIndex = history.lastIndexOf(currentRoute);

        if (existingIndex === history.length - 1) {
            return;
        }

        if (existingIndex >= 0) {
            writeRouteHistory(history.slice(0, existingIndex + 1));
            return;
        }

        writeRouteHistory([...history, currentRoute]);
    }, [currentRoute]);

    const handleBack = () => {
        const history = readRouteHistory();
        if (history.length > 1) {
            writeRouteHistory(history.slice(0, -1));
            router.back();
            return;
        }
        const fallbackRoute = fallbackRouteFor(pathname);
        writeRouteHistory([fallbackRoute]);
        router.push(fallbackRoute);
    };

    if (!shouldShowBackButton(pathname)) {
        return null;
    }

    return (
        <Button
            type="button"
            variant="outline"
            aria-label="Go back"
            onClick={handleBack}
            className="group h-9 w-9 shrink-0 rounded-full border border-primary/20 bg-primary/10 p-0 text-primary shadow-[0_8px_18px_-16px_rgba(60,47,143,0.35)] transition-all duration-200 ease-out hover:scale-[1.04] hover:border-primary/45 hover:bg-primary/90 hover:text-white hover:shadow-[0_0_0_4px_rgba(60,47,143,0.10),0_12px_28px_-16px_rgba(60,47,143,0.75)] focus-visible:ring-primary/25"
        >
            <ArrowLeft className="h-4 w-4 transition-transform duration-200 ease-out group-hover:-translate-x-0.5" />
        </Button>
    );
}
