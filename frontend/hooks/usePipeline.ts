"use client";

import { useMutation } from "@tanstack/react-query";
import { API } from "@/lib/api/endpoints";
import { request } from "@/lib/api/request";
import type {
  PipelineApproveRequest,
  PipelineEditImageTextRequest,
  PipelineEditImageTextResponse,
  PipelineRejectRequest,
  PipelineRunRequest,
  PipelineRunResponse,
} from "@/lib/api/contracts";

const TRANSIENT = new Set(["pending", "running", "generating"]);

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForPipelineRun(runId: string): Promise<PipelineRunResponse> {
  const deadline = Date.now() + 1_100_000;
  while (Date.now() < deadline) {
    const current = await request<void, PipelineRunResponse>(API.PIPELINE.STATUS, {
      pathParams: runId,
    });
    if (!TRANSIENT.has(current.status)) {
      return current;
    }
    await sleep(1500);
  }
  throw new Error("Pipeline timed out waiting for a terminal status.");
}

export function usePipeline() {
  const runPipeline = useMutation({
    mutationFn: async (data: PipelineRunRequest) => {
      const first = await request<PipelineRunRequest, PipelineRunResponse>(API.PIPELINE.RUN, {
        data,
      });
      if (!first.run_id || !TRANSIENT.has(first.status)) {
        return first;
      }
      return waitForPipelineRun(first.run_id);
    },
  });

  const approveBlueprint = useMutation({
    mutationFn: async (data: PipelineApproveRequest) => {
      const first = await request<PipelineApproveRequest, PipelineRunResponse>(API.PIPELINE.APPROVE, {
        data,
      });
      if (!first.run_id || !TRANSIENT.has(first.status)) {
        return first;
      }
      return waitForPipelineRun(first.run_id);
    },
  });

  const rejectBlueprint = useMutation({
    mutationFn: (data: PipelineRejectRequest) =>
      request<PipelineRejectRequest, PipelineRunResponse>(API.PIPELINE.REJECT, { data }),
  });

  const editImageText = useMutation({
    mutationFn: (data: PipelineEditImageTextRequest) =>
      request<PipelineEditImageTextRequest, PipelineEditImageTextResponse>(
        API.PIPELINE.EDIT_IMAGE_TEXT,
        { data },
      ),
  });

  return {
    runPipeline,
    approveBlueprint,
    rejectBlueprint,
    editImageText,
    isLoading: runPipeline.isPending || approveBlueprint.isPending,
    isApproving: approveBlueprint.isPending,
    isEditingImage: editImageText.isPending,
    error: runPipeline.error || approveBlueprint.error || rejectBlueprint.error || editImageText.error,
    data: approveBlueprint.data ?? runPipeline.data,
  };
}
