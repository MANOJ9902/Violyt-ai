# Brand Space Creation Field Inventory

## Purpose

This document records the current Brand Space creation and edit fields. It is based on the supplied UI screenshots and cross-checked against the current frontend form definitions.

The screenshots directly show Brand Foundations, Brand Voice & Emotion, Audience Persona Mapping, Do's & Don'ts, Prompt Intelligence Setup, Content Objectives, and most of Visual Identity. Core Brand Signals, Brand Knowledge Upload, and the lower Visual Identity upload area are included from the current form implementation so the inventory is complete.

## Brand Space Creation

### Core Brand Signals

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Upload Brand Logo | Single file upload | Yes | Accepted: SVG, PNG, JPG, PDF, PPT, PPTX, JPEG, TXT, DOCX. |
| Brand Name | Text input | Yes | Brand name. |
| Tagline | Text input | Yes | Brand tagline. |
| Brand Description | Text area | Yes | Brand description. |
| Industry Category | Dropdown | Yes | Technology / SaaS, Financial Services, Healthcare, Retail/E-commerce, FMCG, Education, Real Estate, Automotive, Hospitality, Media & Entertainment, Manufacturing, Energy, Telecommunications, Professional Services, Government / Public Sector, Nonprofit / NGO, other. |
| Key Differentiators | Text area | No | What makes the brand different. |

### Brand Foundations

#### Brand Purpose and Positioning

| Field | Control | Required |
| --- | --- | --- |
| Brand Mission | Text input | No |
| Brand Vision | Text input | No |
| Brand Promise | Text input | No |
| Market Positioning | Text input | No |
| Role of Digital Platforms | Text input | No |
| Social Media Challenges | Text input | No |

#### Strategic Block

| Field | Control | Required |
| --- | --- | --- |
| Business Problem or Opportunity | Text input | No |
| Perception Challenge | Text input | No |
| Human Insight | Text input | No |
| Brand Advantage | Text input | No |
| Strategy | Text area | No |

#### Industry and Context Parameters

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Brand Archetype | Dropdown | No | Hero, Innovator, Caregiver, Explorer, Creator, Sage, Rebel, Entertainer, Everyman, Ruler, Lover, Magician. |
| Compliance Level | Dropdown | No | Low, Medium, High. |
| Competitor Brands | Repeatable group, maximum three | No | Each competitor has the fields below. |
| Competitor Brand Name | Text input | No | Per competitor. |
| Website URL | Text input | No | Per competitor. |
| LinkedIn | Text input | No | Per competitor social profile. |
| Instagram | Text input | No | Per competitor social profile. |
| X | Text input | No | Per competitor social profile. |

### Brand Voice & Emotion

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Core Tone Attributes | Multi-select checkbox list | Yes | Professional / Formal, Bold, Premium, Playful, Authoritative, Empathetic, Inspirational, Trust Worthy, Polite, Witty. |
| Tone weight | Slider | Conditional | One 0-100% slider for every selected core tone attribute. |
| Primary Emotion | Text input | No | Advanced field. |
| Secondary Emotion | Text input | No | Advanced field. |
| Avoided Emotion | Text input | No | Advanced field. |
| Content Complexity | Dropdown | No | Basic, Expert. |
| Sentence Length | Dropdown | No | Short, Medium, Long, Mixed. |

### Audience Persona Mapping

#### Target Audience and Psychographics

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Select Target Audience | Multi-select checkbox list | Yes | Marketing Leaders, Founders, Investors, Developers, Consumers, CXOs. |
| Goals | Text area | No | Psychographic detail. |
| Motivations | Text area | No | Psychographic detail. |
| Fears and Pain Points | Text area | No | Psychographic detail. |
| Objections | Text area | No | Psychographic detail. |
| Content Consumption Behavior | Text area | No | Psychographic detail. |
| Upload Audience Insights | Multi-file upload | No | Accepted: PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG, WEBP, TXT. |

#### Demographic Details

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Audience Type | Dropdown | No | Consumer, Professional. |
| Location/Region | Dropdown | No | Local, Global. |
| Education Level | Dropdown | No | High School or Below, College / Diploma Educated, University Graduate / Postgraduate Educated, Highly Educated / Academic. |
| Employment Status | Dropdown | No | Student, Early Career Professional, Mid Career Professional, Senior Professional, Executive / Leadership, Entrepreneur / Business Owner, Freelancer / Independent Worker, Homemaker, Retired. |
| Professional Background | Dropdown | No | Technology, Business, Finance, Healthcare, Education, Creative, Sales, Operations, Legal, Entrepreneurship, Skilled Trades, Government, Student, General Audience. |
| Household Size | Dropdown | No | Single Person Household, Couple Household, Small Family (3-4 Members), Large Family (5+ Members), Shared / Multi Generational Household. |
| Language Preference | Dropdown | No | Local Language, Local Language + English, English Preferred, Multilingual Audience. |
| Income Level | Dropdown | No | Low Income, Lower Middle Income, Middle Income, Upper Middle Income, High Income. |
| Family Status or Life Stage | Text input | No | Demographic detail. |
| Socio-economic Segment | Text input | No | Demographic detail. |
| Digital Access | Dropdown | No | Mobile Only, Mobile First, Mobile and Desktop, Multi Device Power User. |

### Do's & Don'ts

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Selected Rules | Multi-select checkbox list | Yes | Avoid emojis, Avoid hype claims, Avoid slang, Avoid competitor comparison. |
| Positive Word Bank | Text area | Yes | Words or phrases separated by commas. |
| Upload Positive Word Bank | File upload | No | Accepted: PDF, DOC, DOCX, PNG, JPG, JPEG, PPT, PPTX, TXT. |
| Replaceable Words | Text area | Yes | Use `word - alternative` entries separated by commas. |
| Upload Replaceable Words | File upload | No | Same supported formats as above. |
| Negative Word Bank | Text area | Yes | Words or phrases separated by commas. |
| Upload Negative Word Bank | File upload | No | Same supported formats as above. |
| What To Do | Text area | Yes | Required custom AI behaviors. |
| What NOT To Do | Text area | Yes | Required forbidden AI behaviors. |
| Restricted Topics | Text area | Yes | Topics the AI must avoid. |
| Restricted Claims | Text area | Yes | Claims the AI must not make. |
| Blocked Words / Phrases | Text area | Yes | Words or phrases the AI must not use. |

### Brand Knowledge Upload

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Template | Multi-file upload | No | Accepted: PDF, JPG, PNG, DOCX, PPT, PPTX, JPEG, TXT; supports local and Google Drive upload. |
| Other Documentation | Multi-file upload | No | Same supported formats and upload behavior. |

### Prompt Intelligence Setup

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Preferred Platforms | Multi-select pill controls | No | LinkedIn, Instagram, X (Twitter), YouTube, Facebook, TikTok, Pinterest, Threads. |
| Preferred Content Formats | Multi-select pill controls | No | Short-form post, Long-form article, Carousel, Reel / Short video, Story, Newsletter, Thread, Infographic caption. |
| Content Tone Override | Text input | No | Instruction override. |
| Platform-Specific Rules | Text area | No | Instruction override. |
| Contextual Hints | Text area | No | Instruction override. |
| Instruction Overrides (Global) | Text area | No | Instruction override. |
| Formats to Avoid | Text input | No | Instruction override. |

### Content Objectives

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Primary Objective | Dropdown | No | Brand Awareness, Lead Generation, Sales Conversion, Community Building, Product Launch, Thought Leadership, Customer Retention, Employer Branding. |
| Content Goal | Dropdown | No | Educate, Inspire, Entertain, Convert, Inform, Engage, Nurture. |
| Campaign Theme | Text input | No | Campaign focus. |
| Business Outcome | Text area | No | Intended outcome. |
| Call to Action | Text input | No | Desired user prompt. |
| Target Conversion Action | Text input | No | Example: trial signup or product purchase. |
| Content Frequency | Dropdown | No | Daily, 3x per week, Weekly, Bi-weekly, Monthly, Campaign-based. |
| Primary Success Metric | Dropdown | No | Reach / Impressions, Engagement Rate, Clicks / CTR, Conversions, Follower Growth, Share of Voice, Revenue Impact. |

### Visual Identity

#### Brand Visual Guidelines

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Brand Mood | Text area | No | Overall mood. |
| Visual Style | Text area | No | Visual direction. |
| Logo Placement | Single-select radio group | Yes | Top - Right, Top - Left, Top - Center, Bottom - Right, Bottom - Left, Bottom - Center, Center. |
| Primary Color | HEX color input | Yes | Color palette. |
| Secondary Color | HEX color input | Yes | Color palette. |
| Additional Colors | Repeatable color name and HEX pair | No | Users can add or remove rows. |
| Upload Color Palette | Multi-file upload | No | Accepted: DOCX, PDF, PPT, PPTX, JPG, JPEG, PNG, TXT. |
| Font | Font selector or upload | Yes | Supports Google Fonts and local font files. |
| Upload Font Style Guide | Single file upload | No | Accepted: DOCX, PDF, PPT, PPTX, JPG, JPEG, PNG, TXT. |

#### Upload Documentation

| Field | Control | Required | Notes |
| --- | --- | --- | --- |
| Reference Creatives | Multi-file upload with metadata tags | Yes | Accepted: PDF, JPG, PNG, DOCX, PPT, PPTX, JPEG, TXT; 25 MB maximum per file; supports local and Google Drive upload. |
| Mood Boards | Multi-file upload with metadata tags | Yes | Same upload behavior as Reference Creatives. |

### Review

The Review tab presents the completed Brand Space for review. It does not add a separate editable field set.

## Current Hidden or Internal Fields

These fields exist in form state or persistence but are not exposed as active controls in the current creation UI:

| Field | Status |
| --- | --- |
| Voice perspective | UI control is commented out. |
| Audience age range | UI control is not rendered. |
| Audience gender | UI control is commented out. |
| Market maturity | UI control is commented out. |
| Buying stage | UI control is commented out. |
| Primary competitor mirror fields | Internal legacy mirrors of the first item in the repeatable competitor list. |
| Active color palette upload ID | Derived selection referring to a color-palette upload. |

## Template Relationship

The current downloadable Brand Space Word template contains an intentional subset of 47 manual fields. It does not include uploads, repeatable structured objects, hidden fields, or all visible optional fields. Template field changes should remain explicit and must preserve the existing upload/download mapping contract.
