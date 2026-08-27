"use client";

import { useMemo } from "react";
import axios from "axios";
import { useBrand, useBrandOverview, useBrands } from "@/hooks/useBrands";
import { mapBrandOverviewToForm } from "@/lib/brand-mappers";
import { resolveBrandByRouteKey } from "@/lib/brand-routing";
import type { BrandFormState } from "@/types/brand-space.types";

function isUuid(value: string) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

export function formatBrandSpaceLoadError(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }
          if (item && typeof item === "object" && "msg" in item) {
            return String(item.msg);
          }
          return "";
        })
        .filter(Boolean)
        .join(", ");
    }
    return error.message || fallback;
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}

export function useBrandSpacePageState(routeKey: string | undefined) {
  const normalizedRouteKey = routeKey?.trim() || "";
  const {
    data: brands,
    isPending: isBrandsPending,
    isError: isBrandsError,
    error: brandsError,
    refetch: refetchBrands,
  } = useBrands();

  const brandFromList = useMemo(
    () => resolveBrandByRouteKey(brands, normalizedRouteKey),
    [brands, normalizedRouteKey],
  );

  const fallbackBrandId =
    !brandFromList && normalizedRouteKey && isUuid(normalizedRouteKey) ? normalizedRouteKey : "";
  const {
    data: brandById,
    isPending: isBrandByIdPending,
    isError: isBrandByIdError,
    error: brandByIdError,
    refetch: refetchBrandById,
  } = useBrand(fallbackBrandId);

  const brand = brandFromList ?? brandById ?? null;
  const brandId = brand?.id || "";

  const {
    data: overview,
    isPending: isOverviewPending,
    isError: isOverviewError,
    error: overviewError,
    refetch: refetchOverview,
  } = useBrandOverview(brandId);

  const initialForm = useMemo<BrandFormState | null>(() => {
    if (!overview) {
      return null;
    }
    try {
      return mapBrandOverviewToForm(overview);
    } catch (error) {
      console.error("Failed to map Brand Space overview into form state", error);
      return null;
    }
  }, [overview]);

  const isResolvingBrand =
    isBrandsPending || (Boolean(fallbackBrandId) && isBrandByIdPending && !brandFromList);
  const isLoadingOverview = Boolean(brandId) && isOverviewPending;
  const isLoading = isResolvingBrand || isLoadingOverview;

  const mappingFailed = Boolean(overview) && !initialForm;

  const loadError = isBrandsError
    ? formatBrandSpaceLoadError(brandsError, "Unable to load Brand Spaces.")
    : isBrandByIdError
      ? formatBrandSpaceLoadError(brandByIdError, "Unable to load this Brand Space.")
      : isOverviewError
        ? formatBrandSpaceLoadError(overviewError, "Unable to load Brand Space details.")
        : mappingFailed
          ? "Brand Space data loaded but could not be opened. Try refreshing the page."
          : null;

  const retry = async () => {
    const tasks: Array<Promise<unknown>> = [];
    if (isBrandsError) {
      tasks.push(refetchBrands());
    }
    if (isBrandByIdError) {
      tasks.push(refetchBrandById());
    }
    if (isOverviewError || mappingFailed) {
      tasks.push(refetchOverview());
    }
    if (!tasks.length && !brand) {
      tasks.push(refetchBrands());
      if (fallbackBrandId) {
        tasks.push(refetchBrandById());
      }
    }
    await Promise.all(tasks);
  };

  return {
    brand,
    overview,
    initialForm,
    isLoading,
    isNotFound: !isLoading && !loadError && !brand,
    loadError,
    retry,
  };
}
