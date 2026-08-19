"use client";

import { useParams } from "next/navigation";
import WorkspaceChat from "@/components/chat/WorkspaceChat";

/**
 * Active Brand Space workspace = Chat Studio.
 * Edit lives at /brand_space/edit/[brandSlug]
 * View lives at /brand_space/view/[brandSlug]
 */
export default function BrandWorkspacePage() {
  const params = useParams<{ brandSlug: string }>();
  return <WorkspaceChat brandKey={params.brandSlug} />;
}
