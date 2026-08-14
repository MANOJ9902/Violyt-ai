import type { CreativeBlueprintResponse, StructuredTextPayload } from "@/lib/api/contracts";

function normalizeTags(hashtags: string[] | undefined): string[] {
  return (hashtags || [])
    .map((tag) => String(tag || "").trim())
    .filter(Boolean)
    .map((tag) => (tag.startsWith("#") ? tag : `#${tag.replace(/^#+/, "")}`));
}

function buildFallbackCaption({
  platform,
  blueprint,
  generatedPayload,
}: {
  platform: string;
  blueprint?: CreativeBlueprintResponse | null;
  generatedPayload?: StructuredTextPayload | null;
}): string {
  const hook = blueprint?.hook?.trim() || "";
  const headline = generatedPayload?.headline?.trim() || blueprint?.headline?.trim() || "";
  const body = generatedPayload?.body?.trim() || blueprint?.body?.trim() || "";
  const supporting = blueprint?.supporting_line?.trim() || "";
  const cta = generatedPayload?.cta?.trim() || blueprint?.cta?.trim() || "";
  const storyFlow = (blueprint?.story_flow || []).map((line) => String(line || "").trim()).filter(Boolean);
  const proofPoints = (blueprint?.proof_points || []).map((line) => String(line || "").trim()).filter(Boolean);
  const hashtags = normalizeTags(
    generatedPayload?.hashtags?.length ? generatedPayload.hashtags : blueprint?.hashtags,
  );

  const normalized = platform === "x" ? "twitter" : platform;
  const paragraphs: string[] = [];
  const lead = hook || headline;
  if (lead) paragraphs.push(lead);

  for (const line of storyFlow.slice(0, 5)) {
    if (!paragraphs.includes(line)) paragraphs.push(line);
  }
  if (supporting && !paragraphs.includes(supporting)) paragraphs.push(supporting);

  if (body) {
    const chunks = body.includes("\n\n") ? body.split("\n\n").map((c) => c.trim()).filter(Boolean) : [body];
    for (const chunk of chunks) {
      if (!paragraphs.includes(chunk)) {
        paragraphs.push(normalized === "twitter" && chunk.length > 220 ? `${chunk.slice(0, 217).trim()}…` : chunk);
      }
    }
  }

  for (const point of proofPoints.slice(0, 2)) {
    if (!paragraphs.includes(point)) paragraphs.push(point);
  }

  if (cta && !paragraphs.some((p) => p.toLowerCase().includes(cta.toLowerCase()))) {
    paragraphs.push(cta);
  }

  if (!paragraphs.some((p) => p.includes("?"))) {
    const topic = headline || hook || "this";
    paragraphs.push(`What stands out to you about ${topic.replace(/\?+$/, "")}?`);
  }

  if (hashtags.length) {
    const limit = normalized === "linkedin" ? 5 : normalized === "instagram" ? 8 : 3;
    paragraphs.push(hashtags.slice(0, limit).join(" "));
  }

  return paragraphs.join("\n\n").trim();
}

export function buildPostCaption({
  platform,
  blueprint,
  generatedPayload,
}: {
  platform: string;
  blueprint?: CreativeBlueprintResponse | null;
  generatedPayload?: StructuredTextPayload | null;
}): string {
  const fromBlueprint = String(blueprint?.post_caption || "").trim();
  if (fromBlueprint) {
    return fromBlueprint;
  }
  return buildFallbackCaption({ platform, blueprint, generatedPayload });
}
