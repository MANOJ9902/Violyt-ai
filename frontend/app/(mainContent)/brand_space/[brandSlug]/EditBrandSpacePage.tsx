"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import BrandSpaceEditor from "@/components/brandSpaces/BrandSpaceEditor";
import { BrandSpacePageStatus } from "@/components/brandSpaces/BrandSpacePageStatus";
import { useBrandSpacePageState } from "@/hooks/useBrandSpacePageState";
import { useRBAC } from "@/hooks/useRBAC";
import { buildBrandViewHref } from "@/lib/brand-routing";

export default function EditBrandSpacePage() {
  const params = useParams<{ brandSlug: string }>();
  const router = useRouter();
  const { user, isPending: isAuthPending, can } = useRBAC();
  const { brand, overview, initialForm, isLoading, isNotFound, loadError, retry } = useBrandSpacePageState(
    params.brandSlug,
  );
  const canEditBrandSpace = Boolean(user && can("BRAND_SPACE", "EDIT"));

  useEffect(() => {
    if (!user || !brand || canEditBrandSpace) {
      return;
    }
    router.replace(buildBrandViewHref(brand));
  }, [brand, canEditBrandSpace, router, user]);

  if (isAuthPending || isLoading) {
    return <BrandSpacePageStatus message="Loading Brand Space..." />;
  }

  if (user && brand && !canEditBrandSpace) {
    return <BrandSpacePageStatus message="Opening read-only Brand Space..." />;
  }

  if (loadError) {
    return (
      <BrandSpacePageStatus
        tone="error"
        message={loadError}
        actionLabel="Try again"
        onAction={() => {
          void retry();
        }}
      />
    );
  }

  if (isNotFound || !brand || !overview || !initialForm) {
    return (
      <BrandSpacePageStatus
        tone="error"
        message="Brand Space not found or you do not have access to it."
        actionLabel="Back to Brand Spaces"
        onAction={() => router.push("/brand_space")}
      />
    );
  }

  return (
    <BrandSpaceEditor
      mode="edit"
      brandId={brand.id}
      initialForm={initialForm}
      initialLifecycleState={overview.brand.lifecycle_state}
    />
  );
}
