"use client";

import { useEffect } from "react";

const RETRY_KEY = "violyt-brand-space-404-retry";

export default function NotFound() {
  useEffect(() => {
    const path = window.location.pathname;
    if (path !== "/brand_space" && !path.startsWith("/brand_space/")) {
      return;
    }

    const alreadyRetried = sessionStorage.getItem(RETRY_KEY) === path;
    if (!alreadyRetried) {
      sessionStorage.setItem(RETRY_KEY, path);
      window.location.replace(window.location.href);
      return;
    }

    if (path !== "/brand_space") {
      sessionStorage.removeItem(RETRY_KEY);
      window.location.replace("/brand_space");
    }
  }, []);

  return (
    <div className="flex h-screen flex-col items-center justify-center">
      <h1 className="mb-4 text-4xl font-bold">404 - Not Found</h1>
      <p className="text-lg text-gray-600">The page you are looking for does not exist.</p>
      <a
        href="/brand_space"
        className="mt-4 rounded bg-blue-500 px-4 py-2 text-slate-100 hover:bg-blue-600"
      >
        Back to Brand Space
      </a>
    </div>
  );
}
