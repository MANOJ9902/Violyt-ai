import { ChevronDown, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

import {
    AddMoreButton,
    AdvancedSectionTitle,
    FileUploadCollection,
    FormField,
    FormSection,
    FormSubsection,
    StyledInput,
    StyledSelect,
    StyledTextarea,
} from "./FormFields";
import {
    AUDIENCE_TYPE_OPTIONS,
    DIGITAL_ACCESS_OPTIONS,
    EDUCATION_LEVEL_OPTIONS,
    EMPLOYMENT_STATUS_OPTIONS,
    HOUSEHOLD_SIZE_OPTIONS,
    INCOME_LEVEL_OPTIONS,
    LANGUAGE_PREFERENCE_OPTIONS,
    LOCATION_OPTIONS,
    PROFESSIONAL_BACKGROUND_OPTIONS,
} from "@/lib/brand-space-options";
import { GLOBAL_COUNTRIES, INDIAN_STATES_AND_UNION_TERRITORIES } from "@/lib/geography-options";
import {
    createBrandUploadItem,
    updateBrandFormSection,
    type BrandTabProps,
} from "@/types/brand-space.types";

function hasMissingAdvancedFields(form: BrandTabProps["form"]) {
    const fields = [
        form.targetAudience.goals,
        form.targetAudience.motivations,
        form.targetAudience.fearsAndPainPoints,
        form.targetAudience.objections,
        form.targetAudience.contentConsumptionBehavior,
        form.targetAudience.audienceType,
        form.targetAudience.location,
        ...(form.targetAudience.location ? [form.targetAudience.locationDetail] : []),
        form.targetAudience.educationLevel,
        form.targetAudience.employmentStatus,
        form.targetAudience.professionalBackground,
        form.targetAudience.householdSize,
        form.targetAudience.languagePreference,
        form.targetAudience.incomeLevel,
        form.targetAudience.familyStatusOrLifeStage,
        form.targetAudience.socioEconomicSegment,
        form.targetAudience.digitalAccess,
    ];
    return fields.some((value) => !String(value || "").trim()) || form.targetAudience.audienceInsights.length === 0;
}
const TargetAudience = ({ form, setForm, onRemoveUpload }: BrandTabProps) => {
    const audienceNames = form.targetAudience.selectedAudiences.length
        ? form.targetAudience.selectedAudiences
        : [""];

    const updateAudience = (index: number, value: string) => {
        const selectedAudiences = [...audienceNames];
        selectedAudiences[index] = value;
        updateBrandFormSection(setForm, "targetAudience", "selectedAudiences", selectedAudiences);
    };

    const addAudience = () => {
        updateBrandFormSection(setForm, "targetAudience", "selectedAudiences", [...audienceNames, ""]);
    };

    const removeAudience = (index: number) => {
        updateBrandFormSection(
            setForm,
            "targetAudience",
            "selectedAudiences",
            audienceNames.filter((_, audienceIndex) => audienceIndex !== index),
        );
    };
    const updateField = <TKey extends keyof typeof form.targetAudience>(
        key: TKey,
        value: (typeof form.targetAudience)[TKey],
    ) => updateBrandFormSection(setForm, "targetAudience", key, value);
    const [isLocationPanelOpen, setIsLocationPanelOpen] = useState(false);
    const updateLocationMode = (value: string) => {
        setForm((current) => ({
            ...current,
            targetAudience: {
                ...current.targetAudience,
                location: value,
                locationDetail: current.targetAudience.location === value
                    ? current.targetAudience.locationDetail
                    : "",
            },
        }));
    };

    const addAudienceInsights = (files: FileList | null) => {
        if (!files?.length) {
            return;
        }
        updateField("audienceInsights", [
            ...form.targetAudience.audienceInsights,
            ...Array.from(files).map((file) => createBrandUploadItem(file)),
        ]);
    };

    return (
        <div className="space-y-8">
            <FormSubsection
                title="Audience"
                description="Who does your brand primarily communicate with?"
                className="bg-[#E9E9E966] px-6 pb-6"
            >
                <div className="space-y-3">
                    {audienceNames.map((audienceName, index) => (
                        <div key={`audience-${index}`} className="flex w-full items-center gap-2">
                            <StyledInput
                                placeholder="Audience Name"
                                value={audienceName}
                                onChange={(event) => updateAudience(index, event.target.value)}
                                className="min-w-0 flex-1 bg-section-input-field"
                            />
                            {index > 0 ? (
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="icon-sm"
                                    onClick={() => removeAudience(index)}
                                    className="size-7 shrink-0 p-0 active:translate-y-0"
                                    aria-label={`Remove audience ${index + 1}`}
                                >
                                    <X className="h-3.5 w-3.5" />
                                </Button>
                            ) : (
                                <span className="size-7 shrink-0" aria-hidden="true" />
                            )}
                        </div>
                    ))}
                    <div className="flex justify-end">
                        <AddMoreButton onClick={addAudience} />
                    </div>
                </div>
            </FormSubsection>
            <FormSubsection title={<AdvancedSectionTitle showInfo={hasMissingAdvancedFields(form)} />} description="Optional fields to further refine your brand intelligence"
                className="bg-[#E9E9E966] px-6 pb-6"
            >
                <div className="grid gap-8 lg:grid-cols-2">
                    <div className="space-y-5 max-w-md rounded-md">
                        <h4 className="text-lg font-semibold text-slate-800">Psychographic Details</h4>
                        <FormField label="Goals">
                            <StyledTextarea
                                className="bg-section-input-field"
                                placeholder="What the persona wants to achieve"
                                value={form.targetAudience.goals}
                                onChange={(e) => updateField("goals", e.target.value)}
                            />
                        </FormField>
                        <FormField label="Motivations">
                            <StyledTextarea
                                className="bg-section-input-field"
                                placeholder="What drives the persona"
                                value={form.targetAudience.motivations}
                                onChange={(e) => updateField("motivations", e.target.value)}
                            />
                        </FormField>
                        <FormField label="Fears and Pain Points">
                            <StyledTextarea
                                className="bg-section-input-field"
                                placeholder="What concerns or frustrates the persona"
                                value={form.targetAudience.fearsAndPainPoints}
                                onChange={(e) => updateField("fearsAndPainPoints", e.target.value)}
                            />
                        </FormField>
                        <FormField label="Objections">
                            <StyledTextarea
                                className="bg-section-input-field"
                                placeholder="What the persona may object"
                                value={form.targetAudience.objections}
                                onChange={(e) => updateField("objections", e.target.value)}
                            />
                        </FormField>
                        <FormField label="Content Consumption Behavior">
                            <StyledTextarea
                                className="bg-section-input-field"
                                placeholder="How the persona consumes content"
                                value={form.targetAudience.contentConsumptionBehavior}
                                onChange={(e) => updateField("contentConsumptionBehavior", e.target.value)}
                            />
                        </FormField>
                        <FileUploadCollection
                            label="Upload Audience Insights"
                            acceptedFormats="PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG, WEBP, TXT"
                            bgColor="bg-[#FFFFFF]"
                            items={form.targetAudience.audienceInsights}
                            onAdd={addAudienceInsights}
                            onRemove={(itemId) => {
                                if (onRemoveUpload) {
                                    void onRemoveUpload(itemId);
                                    return;
                                }
                                updateField(
                                    "audienceInsights",
                                    form.targetAudience.audienceInsights.filter((item) => item.id !== itemId),
                                );
                            }}
                            multiple
                        />
                    </div>

                    <div className="space-y-5 max-w-md">
                        <h4 className="text-lg font-semibold text-slate-800">Demographic Details</h4>
                        <FormField label="Audience Type">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.audienceType}
                                onValueChange={(value) => updateField("audienceType", value)}
                                placeholder="Select audience type"
                                options={AUDIENCE_TYPE_OPTIONS}
                            />
                        </FormField>
                        {/* <FormField label="Gender">
              <StyledInput
                placeholder="Enter gender"
                value={form.targetAudience.gender}
                onChange={(e) => updateField("gender", e.target.value)}
              />
            </FormField> */}
                        <FormField label="Location/Region">
                            <div className="overflow-hidden rounded-xl border border-[#E3E1F3] bg-white">
                                <button
                                    type="button"
                                    className="flex min-h-12 w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-[#FAF9FF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/25"
                                    aria-expanded={isLocationPanelOpen}
                                    aria-controls="location-region-panel"
                                    onClick={() => setIsLocationPanelOpen((open) => !open)}
                                >
                                    <span className="min-w-0 truncate text-sm font-medium text-[#2C2C2C]">
                                        {form.targetAudience.location
                                            ? [form.targetAudience.location, form.targetAudience.locationDetail].filter(Boolean).join(" · ")
                                            : "Choose location and region"}
                                    </span>
                                    <ChevronDown
                                        className={isLocationPanelOpen
                                            ? "h-4 w-4 shrink-0 rotate-180 text-primary transition-transform"
                                            : "h-4 w-4 shrink-0 text-primary transition-transform"}
                                        aria-hidden="true"
                                    />
                                </button>

                                {isLocationPanelOpen ? (
                                    <div id="location-region-panel" className="border-t border-[#EDEAFB]">
                                        {LOCATION_OPTIONS.map((mode) => {
                                            const isSelectedMode = form.targetAudience.location === mode;
                                            const isGlobal = mode === "Global";
                                            const options = isGlobal
                                                ? GLOBAL_COUNTRIES
                                                : INDIAN_STATES_AND_UNION_TERRITORIES;
                                            const detailLabel = isGlobal ? "Countries" : "Indian States & Union Territories";

                                            return (
                                                <div key={mode} className={isGlobal ? "border-t border-[#EDEAFB]" : ""}>
                                                    <label
                                                        className={isSelectedMode
                                                            ? "flex cursor-pointer items-center gap-2.5 bg-[#F8F6FF] px-4 py-3 text-sm font-medium text-primary transition"
                                                            : "flex cursor-pointer items-center gap-2.5 px-4 py-3 text-sm text-[#4B4B4B] transition hover:bg-[#FBFAFF]"}
                                                    >
                                                        <input
                                                            type="radio"
                                                            name="location-mode"
                                                            value={mode}
                                                            checked={isSelectedMode}
                                                            onChange={() => updateLocationMode(mode)}
                                                            className="h-4 w-4 shrink-0 accent-primary"
                                                        />
                                                        {mode}
                                                    </label>

                                                    {isSelectedMode ? (
                                                        <div className="border-t border-[#EEEAFB] bg-[#FCFBFF] px-3 py-2.5">
                                                            <p className="px-1 pb-2 text-xs font-medium text-[#77708F]">{detailLabel}</p>
                                                            <div
                                                                role="radiogroup"
                                                                aria-label={detailLabel}
                                                                className="max-h-60 space-y-0.5 overflow-y-auto pr-1"
                                                            >
                                                                {options.map((option) => {
                                                                    const isSelectedOption = form.targetAudience.locationDetail === option;
                                                                    return (
                                                                        <label
                                                                            key={option}
                                                                            className={isSelectedOption
                                                                                ? "flex cursor-pointer items-center gap-2.5 rounded-lg bg-primary/10 px-2.5 py-2 text-sm font-medium text-primary transition"
                                                                                : "flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-[#4B4B4B] transition hover:bg-[#F4F1FF]"}
                                                                        >
                                                                            <input
                                                                                type="radio"
                                                                                name="location-detail"
                                                                                value={option}
                                                                                checked={isSelectedOption}
                                                                                onChange={() => updateField("locationDetail", option)}
                                                                                className="h-4 w-4 shrink-0 accent-primary"
                                                                            />
                                                                            <span className="min-w-0 break-words">{option}</span>
                                                                        </label>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    ) : null}
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : null}
                            </div>
                        </FormField>                        <FormField label="Education Level">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.educationLevel}
                                onValueChange={(value) => updateField("educationLevel", value)}
                                placeholder="Select education level"
                                options={EDUCATION_LEVEL_OPTIONS}
                            />
                        </FormField>
                        <FormField label="Employment Status">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.employmentStatus}
                                onValueChange={(value) => updateField("employmentStatus", value)}
                                placeholder="Select employment status"
                                options={EMPLOYMENT_STATUS_OPTIONS}
                            />
                        </FormField>
                        <FormField label="Professional Background">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.professionalBackground}
                                onValueChange={(value) => updateField("professionalBackground", value)}
                                placeholder="Select professional background"
                                options={PROFESSIONAL_BACKGROUND_OPTIONS}
                            />
                        </FormField>
                        <FormField label="Household Size">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.householdSize}
                                onValueChange={(value) => updateField("householdSize", value)}
                                placeholder="Number of people in the household"
                                options={HOUSEHOLD_SIZE_OPTIONS}
                            />
                        </FormField>
                        <FormField label="Language Preference">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.languagePreference}
                                onValueChange={(value) => updateField("languagePreference", value)}
                                placeholder="Preferred language"
                                options={LANGUAGE_PREFERENCE_OPTIONS}
                            />
                        </FormField>
                        <FormField label="Income Level">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.incomeLevel}
                                onValueChange={(value) => updateField("incomeLevel", value)}
                                placeholder="Select income range"
                                options={INCOME_LEVEL_OPTIONS}
                            />
                        </FormField>
                        <FormField label="Family Status or Life Stage">
                            <StyledInput
                                className="bg-section-input-field"
                                placeholder="Current family or life stage"
                                value={form.targetAudience.familyStatusOrLifeStage}
                                onChange={(e) => updateField("familyStatusOrLifeStage", e.target.value)}
                            />
                        </FormField>
                        <FormField label="Socio-economic Segment">
                            <StyledInput
                                className="bg-section-input-field"
                                placeholder="Socio economic classification"
                                value={form.targetAudience.socioEconomicSegment}
                                onChange={(e) => updateField("socioEconomicSegment", e.target.value)}
                            />
                        </FormField>
                        <FormField label="Digital Access">
                            <StyledSelect
                                className="bg-section-input-field"
                                value={form.targetAudience.digitalAccess}
                                onValueChange={(value) => updateField("digitalAccess", value)}
                                placeholder="Access to digital platforms and devices"
                                options={DIGITAL_ACCESS_OPTIONS}
                            />
                        </FormField>
                    </div>
                </div>
            </FormSubsection>
        </div>
    );
};

export default TargetAudience;
