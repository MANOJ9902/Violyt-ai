"use client";

import { Button } from "@/components/ui/button";

export function BrandSpacePageStatus({
  message,
  tone = "muted",
  actionLabel,
  onAction,
}: {
  message: string;
  tone?: "muted" | "error";
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="w-full px-6 py-10">
      <p className={tone === "error" ? "text-sm text-red-600" : "text-sm text-slate-500"}>{message}</p>
      {actionLabel && onAction ? (
        <Button type="button" variant="outline" className="mt-4" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
