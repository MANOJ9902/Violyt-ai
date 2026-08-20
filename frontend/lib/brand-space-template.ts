import type { BrandTemplateFieldValue } from "@/lib/api/contracts";
import type { BrandFormState } from "@/types/brand-space.types";

type EditableBrandSection = Exclude<keyof BrandFormState, "brandKnowledge">;
type CompetitorField = "name" | "websiteUrl" | "linkedin" | "instagram" | "x";

const competitorKeyPattern = /^additional\.competitorBrands\.(\d+)\.(name|websiteUrl|linkedin|instagram|x)$/;
const businessModelDetailKeyMap: Record<string, string> = {
  b2b: "B2B",
  b2c: "B2C",
  b2b2c: "B2B2C",
  other: "Other",
};

const routeToMarketDetailKeyMap: Record<string, string> = {
  d2c: "D2C",
  retail: "Retail",
  marketplace: "Marketplace",
  distributor_dealer: "Distributor/Dealer",
  partner_led: "Partner-led",
  direct_sales: "Direct Sales",
  other: "Other",
};

function isToneWeights(value: BrandTemplateFieldValue["value"]): value is Record<string, number> {
  return !Array.isArray(value) && typeof value === "object" && value !== null;
}

function isAdditionalColors(
  value: BrandTemplateFieldValue["value"],
): value is Array<{ name: string; hex: string }> {
  return Array.isArray(value) && value.every((item) =>
    typeof item === "object" && item !== null && "name" in item && "hex" in item,
  );
}

export function applyBrandSpaceTemplateFields(
  form: BrandFormState,
  fields: BrandTemplateFieldValue[],
): BrandFormState {
  const next = structuredClone(form) as BrandFormState;

  for (const field of fields) {
    if (field.key === "targetAudience.selectedAudiences" && typeof field.value === "string") {
      next.targetAudience.selectedAudiences = field.value
        .split(/[\n,;]+/)
        .map((value) => value.trim())
        .filter(Boolean);
      continue;
    }
    const businessDetailKey = field.key.replace("additional.businessModelDetails.", "");
    const businessModel = businessModelDetailKeyMap[businessDetailKey];
    if (businessModel && typeof field.value === "string") {
      next.additional.businessModelDetails = {
        ...next.additional.businessModelDetails,
        [businessModel]: field.value,
      };
      if (businessModel === "Other") {
        next.additional.businessModelOther = field.value;
      }
      continue;
    }
    const routeDetailKey = field.key.replace("additional.routeToMarketDetails.", "");
    const route = routeToMarketDetailKeyMap[routeDetailKey];
    if (route && typeof field.value === "string") {
      next.additional.routeToMarketDetails = {
        ...next.additional.routeToMarketDetails,
        [route]: field.value,
      };
      continue;
    }
    const competitorMatch = field.key.match(competitorKeyPattern);
    if (competitorMatch && typeof field.value === "string") {
      const index = Number(competitorMatch[1]);
      const competitorField = competitorMatch[2] as CompetitorField;
      if (index > 2) {
        continue;
      }
      const competitors = [...next.additional.competitorBrands];
      while (competitors.length <= index) {
        competitors.push({ name: "", websiteUrl: "", linkedin: "", instagram: "", x: "" });
      }
      competitors[index] = { ...competitors[index], [competitorField]: field.value };
      next.additional.competitorBrands = competitors;
      continue;
    }

    if (field.key === "voiceTone.coreToneAttributeWeights" && isToneWeights(field.value)) {
      next.voiceTone.coreToneAttributeWeights = field.value;
      continue;
    }

    if (field.key === "visualIdentity.additionalColors" && isAdditionalColors(field.value)) {
      next.visualIdentity.additionalColors = field.value;
      continue;
    }

    if (field.key === "visualIdentity.logoPlacements" && typeof field.value === "string") {
      next.visualIdentity.logoPlacements = [field.value];
      continue;
    }

    const [sectionName, fieldName, ...rest] = field.key.split(".");
    if (rest.length || !sectionName || !fieldName || sectionName === "brandKnowledge") {
      continue;
    }

    const section = sectionName as EditableBrandSection;
    const target = next[section] as unknown as Record<string, unknown>;
    if (!target || !(fieldName in target)) {
      continue;
    }
    if (Array.isArray(target[fieldName]) && !Array.isArray(field.value)) {
      continue;
    }
    if (!Array.isArray(target[fieldName]) && Array.isArray(field.value)) {
      continue;
    }
    target[fieldName] = field.value;
  }

  const primaryCompetitor = next.additional.competitorBrands[0];
  if (primaryCompetitor) {
    next.additional.competitorBrandName = primaryCompetitor.name;
    next.additional.websiteUrl = primaryCompetitor.websiteUrl;
    next.additional.linkedin = primaryCompetitor.linkedin;
    next.additional.instagram = primaryCompetitor.instagram;
    next.additional.x = primaryCompetitor.x;
  }

  return next;
}
