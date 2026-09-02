"use client";

import { useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import BrandSpaceEditor from "@/components/brandSpaces/BrandSpaceEditor";
import { useBrandOverview, useBrands } from "@/hooks/useBrands";
import { useRBAC } from "@/hooks/useRBAC";
import { mapBrandOverviewToForm } from "@/lib/brand-mappers";
import { buildBrandEditHref, resolveBrandByRouteKey } from "@/lib/brand-routing";

export default function ViewBrandSpacePage() {
  const params = useParams<{ brandSlug: string }>();
  const router = useRouter();
  const { user, can, isPending: isRbacPending } = useRBAC();
  const canEditBrandSpace = Boolean(user && can("BRAND_SPACE", "EDIT"));
  const {
    data: brands,
    isLoading: isBrandsLoading,
    isError: isBrandsError,
    error: brandsError,
  } = useBrands();
  const brand = useMemo(
    () => resolveBrandByRouteKey(brands, params.brandSlug),
    [brands, params.brandSlug],
  );
  const {
    data: overview,
    isLoading: isOverviewLoading,
    isError: isOverviewError,
    error: overviewError,
    refetch: refetchOverview,
  } = useBrandOverview(brand?.id || "");

  const initialForm = useMemo(() => {
    if (!overview) return undefined;
    try {
      return mapBrandOverviewToForm(overview);
    } catch (error) {
      console.error("mapBrandOverviewToForm failed", error);
      return undefined;
    }
  }, [overview]);

  // Editors should land on the editable Brand Space, not a dead read-only page.
  useEffect(() => {
    if (isRbacPending || !brand || !canEditBrandSpace) {
      return;
    }
    router.replace(buildBrandEditHref(brand));
  }, [brand, canEditBrandSpace, isRbacPending, router]);

  if (isRbacPending) {
    return <div className="w-full px-6 py-10 text-sm text-slate-500">Loading Brand Space...</div>;
  }

  if (canEditBrandSpace && brand) {
    return <div className="w-full px-6 py-10 text-sm text-slate-500">Opening Edit Brand Space...</div>;
  }

  if (isBrandsLoading || (Boolean(brand?.id) && isOverviewLoading)) {
    return <div className="w-full px-6 py-10 text-sm text-slate-500">Loading Brand Space...</div>;
  }

  if (isBrandsError) {
    return (
      <div className="w-full px-6 py-10 text-sm text-red-600">
        Could not load Brand Spaces. {brandsError instanceof Error ? brandsError.message : "Please refresh and try again."}
      </div>
    );
  }

  if (!brand) {
    return <div className="w-full px-6 py-10 text-sm text-slate-500">Brand Space not found.</div>;
  }

  if (isOverviewError) {
    const detail =
      overviewError && typeof overviewError === "object" && "response" in overviewError
        ? String((overviewError as { response?: { status?: number; data?: { detail?: string } } }).response?.data?.detail || "")
        : "";
    const status =
      overviewError && typeof overviewError === "object" && "response" in overviewError
        ? (overviewError as { response?: { status?: number } }).response?.status
        : undefined;
    return (
      <div className="w-full space-y-3 px-6 py-10 text-sm text-red-600">
        <p>
          Could not load this Brand Space.
          {status ? ` (HTTP ${status})` : ""}{" "}
          {detail || (overviewError instanceof Error ? overviewError.message : "Please try again.")}
        </p>
        <button
          type="button"
          className="rounded-md border border-slate-300 px-3 py-1.5 text-slate-700"
          onClick={() => void refetchOverview()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!overview || !initialForm) {
    return (
      <div className="w-full px-6 py-10 text-sm text-slate-500">
        Brand Space data could not be opened. Refresh the page or reopen this Brand Space.
      </div>
    );
  }

  return (
    <BrandSpaceEditor
      mode="view"
      brandId={brand.id}
      initialForm={initialForm}
      initialLifecycleState={overview.brand.lifecycle_state}
    />
  );
}
