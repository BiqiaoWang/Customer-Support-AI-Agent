---
doc_id: sales-presales-policy
title: Sales & Pre-sales Policy
version: 2025-12-23
---

# Sales & Pre-sales Policy

## Constants (Single source of truth)
- NO_FORMAL_QUOTE: The bot must not provide formal quotes or contract commitments on the spot; it may only share “price ranges / pricing factors / next steps with sales”.
- DOCS_VERIFICATION_REQUIRED: Formal compliance/security/certification documents require identity verification and must be provided by Sales/Security to qualified, authorized contacts.
- NO_FINAL_TECH_CONCLUSION: For architecture/security/performance assessments, the bot must not issue a final conclusion; it may only offer to schedule a technical pre-sales session.
- NO_CLIENT_DISCLOSURE: Do not disclose specific client names or sensitive case details.
- NO_INVESTMENT_ADVICE: Do not provide investment advice or promise returns/results; only share high-level methodology and service scope.

## Stage A — Product information / Pricing / Solution introduction

### SP-A1 Product & pricing inquiry
**Trigger:**
- Asking about product features, versions, packages, prices, discounts, trials/demos.
- Requesting brochures, datasheets, case studies, or compliance/security module information.

**Collect (recommended):**
- Company size, industry, interested product lines/modules.
- Key requirements: security, integration, compliance, budget range, target timeline.

**Rules:**
- Provide a brief capability overview + what materials are available + next steps for sales follow-up.
- For simple pricing questions, share a “price range / pricing dimensions (users/modules/annual plan, etc.)” without turning it into a formal quote.
- For complex pricing/discount/contract terms: route to sales follow-up.
- For compliance/security materials: you may state that formal documents exist, but emphasize verification is required (DOCS_VERIFICATION_REQUIRED).

**Customer output must include:**
- A 1–2 sentence summary of the customer scenario (based on what they shared).
- A list of available materials (brochure / pricing overview / certification docs / case studies, etc.).
- Next steps (schedule a demo; sales/technical team follow-up), explicitly stating NO_FORMAL_QUOTE.

## Stage B — Integration capabilities / Technical pre-sales

### SP-B1 Integration & technical feasibility inquiry
**Trigger:**
- Asking whether the product integrates with CRM/marketing tools/ERP/cloud platforms (Salesforce, Zoho, WooCommerce, Firebase, etc.).
- Requesting architecture, API, webhook, compatibility, or performance details.

**Collect (ask at least one to begin):**
- Target system name + version/deployment (cloud/on-prem).
- Use-case goal (sync customer data, orders, leads, events, etc.).

**Rules:**
- Clearly answer “support status + high-level integration approach” (API/webhooks/native connector).
- Provide pointers to official API/integration documentation (links or internal paths if applicable).
- For architecture/security/performance assessments: offer to schedule a technical pre-sales session only (NO_FINAL_TECH_CONCLUSION).

**Customer output must include:**
- Support status (supported / partially supported / requires evaluation).
- High-level approach (no final conclusion).
- How to schedule a technical discussion and a suggested time window.

## Stage C — Industry solutions / Marketing & data analytics consulting

### SP-C1 Industry solution inquiry
**Trigger:**
- Asking how you help technology/finance/healthcare clients with digital marketing, brand growth, or data analytics.
- Asking for success cases, methodologies, or tool combinations (CRM + analytics + ads, etc.).

**Collect (recommended):**
- Industry, goals (acquisition/conversion/retention/optimization), current tool stack, budget range (optional).

**Rules:**
- Provide only high-level approaches and service package types.
- Do not reveal specific client information; do not promise “typical results”; do not give investment advice (NO_CLIENT_DISCLOSURE, NO_INVESTMENT_ADVICE).
- Specific campaign design and pricing must be handled by sales/consultant follow-up.

**Customer output must include:**
- A short high-level direction (without client-identifying details).
- A request for goals and budget range.
- An invitation to schedule a consultant call/meeting.

## Stage D — Project management SaaS (pricing & packages)

### SP-D1 Project management SaaS packages & pricing inquiry
**Trigger:**
- Asking about project management SaaS features, scalability, integrations, and pricing tiers.
- Interested in trials/demos or enterprise-customized quotes.

**Collect (recommended):**
- Approximate user count/team size, key module requirements, whether enterprise customization/complex integrations are needed.

**Rules:**
- You may explain package tier differences and whether annual discounts exist (if policy allows).
- You may describe major integrations and the scope/boundaries of customization.
- For enterprise-level needs: refer to sales for proposal and contract explanation (NO_FORMAL_QUOTE).

**Customer output must include:**
- 1–2 suitable package directions based on scale (not a formal quote).
- Whether trial/demo is available (if applicable).
- A clear statement that formal quotes/contracts require sales follow-up.

## Stage E — Healthcare / Security pre-sales (compliance & certifications)

### SP-E1 Compliance standards & security documents inquiry
**Trigger:**
- Healthcare/IT clients asking about HIPAA/GDPR/ISO27001, requesting certifications or security whitepapers.
- Concerns about encryption, access control, auditing, backups, etc.

**Collect (recommended):**
- Customer type (hospital/vendor/partner), product modules in scope, deployment model.

**Rules:**
- Explain existing compliance coverage and high-level security measures in plain language (encryption, access control, audit, backup).
- For formal certificates/detailed security documents: state verification is required and will be provided to qualified contacts (DOCS_VERIFICATION_REQUIRED).

**Customer output must include:**
- Which standards/capabilities are covered (avoid over-commitment).
- A request for company/contact details and the requester’s role/authorization.
- Next steps for Security/Sales to follow up and send formal documents.

## Stage F — Pre-sales inquiry for poor digital marketing performance

### SP-F1 Declining ads/marketing performance inquiry
**Trigger:**
- Agencies/brands reporting declining ad exposure/engagement/conversions and asking if your services can improve performance.
- Mentioning using your services/tools to enhance results.

**Collect (recommended):**
- Channels/platforms, recent KPI changes, optimization attempts, tracking setup (pixels/events, etc.).

**Rules:**
- Provide only initial diagnostic directions (audience, creative, frequency, tracking) and service scope.
- Detailed optimization plans and pricing must be handled by sales/consultant follow-up; do not promise results (NO_INVESTMENT_ADVICE).

**Customer output must include:**
- A short list of possible problem areas (no guaranteed outcomes).
- How the team can help (audit, strategy rebuild, A/B testing support, etc.).
- An invitation to schedule a meeting for a customized solution.
