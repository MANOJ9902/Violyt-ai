"use client";

import { useParams, useSearchParams } from "next/navigation";
import ShareReviewScreen from "@/components/sharing/ShareReviewScreen";

export default function SharingPage() {
  const params = useParams<{ brandSlug: string }>();
  const searchParams = useSearchParams();
  return (
    <ShareReviewScreen
      brandKey={params.brandSlug}
      reviewToken={searchParams.get("token") || undefined}
    />
  );
}
