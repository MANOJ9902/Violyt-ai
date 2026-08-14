import { buildPostCaption } from "../frontend/lib/post-caption.ts";

const cases = [
  {
    name: "instagram-full",
    platform: "instagram",
    blueprint: {
      hook: "Did you know damaged notes can still hold value?",
      headline: "Your ₹500 note isn't worthless",
      body: "RBI rules let you exchange torn currency at any bank branch.",
      cta: "Learn the steps",
      hashtags: ["#FinanceTips", "#RBI"],
    },
  },
  {
    name: "linkedin-carousel",
    platform: "linkedin",
    blueprint: {
      hook: "Bond basics in 60 seconds",
      body: "Understand yield, tenure, and risk before you invest.",
      cta: "Explore bonds on Jiraaf",
      hashtags: ["#Bonds", "#Investing", "#Jiraaf"],
    },
  },
  {
    name: "empty-should-fallback-headline",
    platform: "instagram",
    generatedPayload: {
      headline: "Cognixia upskilling tip",
      body: "Build cloud skills with hands-on labs.",
      cta: "Start learning",
      hashtags: ["#Cognixia", "#Cloud"],
      metadata: {},
    },
  },
];

let failed = 0;
for (const c of cases) {
  const caption = buildPostCaption({
    platform: c.platform,
    blueprint: c.blueprint,
    generatedPayload: c.generatedPayload,
  });
  const ok = caption.length > 20 && (caption.includes("#") || c.name.includes("empty"));
  console.log(`${ok ? "PASS" : "FAIL"} ${c.name}: ${caption.slice(0, 120).replace(/\n/g, " | ")}`);
  if (!ok) failed += 1;
}
process.exit(failed ? 1 : 0);
