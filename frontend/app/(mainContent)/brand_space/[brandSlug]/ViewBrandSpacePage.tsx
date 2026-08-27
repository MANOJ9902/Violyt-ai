"use client";

import { useParams, useRouter } from "next/navigation";
import BrandSpaceEditor from "@/components/brandSpaces/BrandSpaceEditor";
import { BrandSpacePageStatus } from "@/components/brandSpaces/BrandSpacePageStatus";
import { useBrandSpacePageState } from "@/hooks/useBrandSpacePageState";

export default function ViewBrandSpacePage() {
  const params = useParams<{ brandSlug: string }>();
  const router = useRouter();
  const { brand, overview, initialForm, isLoading, isNotFound, loadError, retry } = useBrandSpacePageState(
    params.brandSlug,
  );

  if (isLoading) {
    return <BrandSpacePageStatus message="Loading Brand Space..." />;
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
      mode="view"
      brandId={brand.id}
      initialForm={initialForm}
      initialLifecycleState={overview.brand.lifecycle_state}
    />
  );
}
