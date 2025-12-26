---
doc_id: returns-exchanges-policy
title: Returns & Exchanges Policy
version: 2025-12-23
---

# Returns & Exchanges Policy

## Constants (Single source of truth)
- RETURN_WINDOW_DAYS: 30 days from receipt.
- REFUND_SLA_AFTER_RECEIPT: 5–7 business days after warehouse receives item.
- EXCHANGE_SLA_AFTER_RECEIPT: 5–7 business days after warehouse receives item.
- HUMAN_RESPONSE_SLA: 1–2 business days (only when escalated).

> Note: Always express timelines with a trigger point (“after warehouse receives the item”).
> Do not promise exact dates.

## Stage A — Customer has NOT initiated a return

### RE-A1 Standard return inquiry
**Trigger:** Customer asks how to return/refund, deadline/conditions, shipping fee, etc.

**Ask (required):**
- Order number, purchase/receipt date, product name.
- Condition: unused + original packaging + proof of purchase (if required).

**Rule:**
- Most items must be returned within RETURN_WINDOW_DAYS.
- If NOT defect/incorrect shipment: customer usually pays return shipping; restocking fee may apply (if policy says so).

**Exceptions:**
- Clearance/special products: eligibility depends on item policy → escalate if unclear.

**Customer output must include:**
- Whether they appear eligible (based on info provided).
- How to initiate in portal (do not invent return address in chat).
- Shipping/responsibility & possible fees (neutral wording if uncertain).
- Refund timeline: REFUND_SLA_AFTER_RECEIPT (no tighter promise).

## Stage A — Customer wants an exchange

### RE-A2 Exchange request
**Trigger:** Customer explicitly requests exchange (size/model) or replacement of defective item.

**Ask (required):**
- Order number, product name, purchase date.
- Serial number (if applicable).
- Reason: defect vs incorrect shipment vs preference.

**Eligibility:**
- Within RETURN_WINDOW_DAYS.
- Original packaging + accessories (if required).

**Shipping wording:**
- If responsibility not explicit: “subject to review” (avoid commitment).

**Escalate if:**
- Technical defect needs troubleshooting details.
- Multi-item / ambiguous eligibility.

**Customer output must include:**
- Eligibility summary.
- What must be returned.
- Shipping fee wording.
- Exchange timeline: EXCHANGE_SLA_AFTER_RECEIPT.

## Stage B — Customer initiated return but is blocked / needs RMA / label

### RE-B1 Portal/RMA handling
**Trigger:** Customer asks return address / next step / portal issues / needs RMA.

**Ask (required):**
- Order number OR return reference/RMA.
- Where blocked (login, missing email, unclear RMA, etc.).
- Error screenshots/messages (if any).

**Process steps (explain clearly):**
1) Submit request in portal.
2) System reviews and generates RMA (if applicable).
3) Return address and label provided via portal/email.
4) Warehouse receives item → refund/exchange triggered.

**Exception handling:**
- Portal errors → create internal ticket.
- Provide backup option (e.g., request label via email) but do not guarantee bot can issue it.

**Customer output must include:**
- Exactly where to find RMA/label.
- Next step to unblock.

## Stage C — Status, delays, “have you received it?”

### RE-C1 Status & delay inquiry
**Trigger:** “I sent it but no updates”, “how long until refund”, “did you receive it”.

**Ask (required):**
- Order/return number, shipment date, tracking number.

**Bot logic:**
- If real-time status exists: show received / in transit / processing.
- If cannot retrieve OR exceeds REFUND_SLA_AFTER_RECEIPT → escalate.

**Customer communication:**
- Apologize + neutral assurance.
- Never fabricate dates.

**Escalation output (if escalated):**
- Human follow-up in HUMAN_RESPONSE_SLA.

## Stage D — Refund amount / fee disputes

### RE-D1 Amount dispute
**Trigger:** Customer disputes refund amount, shipping/restocking fee deduction.

**Ask (required):**
- Order number, original paid amount, expected refund amount + reason.

**Rule:**
- Explain preliminary calculation logic only.
- Do not adjust money in bot flow.

**Escalate:**
- All monetary disputes → finance / second-line review.


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

> This structure is intended to be easy to split by `##/###` headers for RAG retrieval. [web:153]

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

**Compliance/security materials:**
- You may state that formal documents exist, but emphasize they require verification and must be provided to authorized contacts (DOCS_VERIFICATION_REQUIRED).

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
- The bot provides only high-level approaches and service package types.
- Do not reveal specific client information; do not promise “typical results”; do not give investment advice (NO_CLIENT_DISCLOSURE, NO_INVESTMENT_ADVICE).
- Specific campaign design and pricing must be handled by sales/consultant follow-up.

**Customer output must include:**
- A short high-level direction (without client-identifying details).
- A request for goals and budget range.
- An invitation to schedule a consultant call/meeting.

## Stage D — Project management SaaS (product-line specific: pricing & packages)

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
- For formal certificates/detailed security documents: state they require verification and will be provided by Security/Sales to qualified contacts (DOCS_VERIFICATION_REQUIRED).

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



---
doc_id: it-technical-support-policy
title: IT & Technical Support Policy
version: 2025-12-23
---

# IT & Technical Support Policy

## Constants (Single source of truth)
- MIN_INFO_REQUIRED: At least one of (error message, timestamp, affected feature) is required to start meaningful troubleshooting.
- NO_FAKE_TIMELINES: Do not invent ETAs. Provide timelines only if an internal status/owner gives one.
- NO_DATA_EXPOSURE: Do not request secrets (passwords, full API keys, private tokens). Ask for masked values only.
- SECURITY_FIRST: Any suspected breach/unauthorized access/vulnerability triggers immediate security escalation.
- STATUS_FIRST_FOR_INCIDENTS: If outage/degradation is suspected, prioritize service restoration/status communication over deep root-cause in the first reply.

## Stage 0 — Scope & routing (internal)
### IT-0A What belongs here
This policy applies to:
- SaaS outages, degradation, crashes, timeouts.
- Dashboard slowness / data refresh issues.
- Integration/API/configuration troubleshooting and documentation requests.
- Software compatibility conflicts.
- Elasticsearch troubleshooting.
- Hardware sizing recommendations.
- Security incident response (breach/vulnerability) and medical-data security hardening requests.

### IT-0B What should be moved to another policy
Move these OUT of IT Technical Support to avoid retrieval confusion:
- “Digital Marketing Strategy Review and Optimization” → Sales/Consulting policy.
- “Industry marketing performance consulting” → Sales/Consulting policy.
(Keep “Investment analytics tool accuracy/configuration” only if it’s a supported product you operate.)

## Stage A — Incidents: outage / degradation / crash (SaaS platform)
### IT-A1 SaaS platform performance, connectivity, integration failure, crashes
**Trigger:**
- Reports of degraded performance, connectivity issues, integration failures, crashes, widespread timeouts.

**Ask (required, minimal):**
- What happened + exact timestamp(s) + error message (copy/paste).
- Scope: single user vs multiple users/locations.
- Environment: OS, browser/app version, network type.
- Recent changes: deployments, config changes, API key rotation (if known).

**Actions (internal):**
- Acknowledge and confirm investigation priority.
- Check service health: server load, network connectivity, logs/alerts.
- Classify: performance vs connectivity vs integration vs crash.
- Provide safe workarounds if available.
- Escalate to engineering/SRE for complex or system-wide cases.
- If core service down: trigger emergency response.

**Customer output must include:**
- Acknowledgment + what info is being checked (high-level).
- Clear request for the single most important missing detail (if any).
- Workaround(s) if safe.
- ETA only if available; otherwise commit to update cadence.

## Stage B — Feature-specific performance (dashboard slowness / refresh delays)
### IT-B1 Project dashboard loading delays
**Trigger:**
- Slow loading, delayed responses, data refresh issues in dashboard.

**Ask (required):**
- Which dashboard/module + approximate load time + timestamp.
- Browser console errors (if web), screenshot (if possible).
- Whether it reproduces on another browser/network.

**Actions (internal):**
- Check recent deployments, traffic spikes, cache effectiveness, DB query latency.
- Apply performance optimizations: caching, query tuning, resource scaling.
- If third-party dependency involved: coordinate with vendor/provider.

**Customer output must include:**
- What’s being investigated (non-sensitive).
- Any immediate mitigation (export/report alternative if available).
- What user data is needed next (if any).

## Stage C — Integration guidance & documentation (API/SDK/setup)
### IT-C1 Integration requests and setup support
**Trigger:**
- Requests for integration guidance, API docs, SDKs, specs, setup support.

**Ask (recommended):**
- Target system(s) + versions + desired data flow (sync direction, frequency).
- Auth method and whether they can access developer settings.

**Rules:**
- Provide official documentation links/paths, supported patterns, prerequisites.
- Explain known limitations: rate limits, formats, feature coverage.
- Offer a technical session for architecture decisions when needed.

**Customer output must include:**
- “Supported / partially supported / not supported” (if known).
- High-level recommended approach + where to find official docs.
- Next steps (test checklist / meeting option).

## Stage D — General troubleshooting (most common path)
### IT-D1 Standard troubleshooting workflow
**Trigger:**
- Generic software errors, configuration issues, intermittent bugs, “it doesn’t work”.

**Ask (required):**
- Error message + steps to reproduce + timestamp.
- Recent changes (updates, config changes).
- Logs/screenshots (where applicable).

**Tiered actions (internal):**
- Basic: restart, cache clear, update, check permissions.
- Intermediate: config adjustment, log review, patch.
- Complex: escalate to senior/engineering with reproduction details.

**Customer output must include:**
- Step-by-step safe checks (only what’s appropriate for their role).
- A clear next action + what evidence to collect if it fails.

## Stage E — Compatibility conflicts (post-update issues)
### IT-E1 Compatibility problems after updates
**Trigger:**
- Conflicts/abnormal behavior after OS/app/plugin updates.

**Ask (required):**
- Versions: OS/app/dependency/plugin/driver.
- When it started + whether rollback is possible.

**Actions (internal):**
- Identify conflict source, provide patch/rollback guidance if supported.
- Recommend prevention: backups, staging/test environment for major changes.

**Customer output must include:**
- Confirmed/likely compatibility factor.
- Safe remediation steps and rollback options (if available).
- Next steps if issue persists (escalation).

## Stage F — Elasticsearch support
### IT-F1 Elasticsearch update/connection/query/indexing issues
**Trigger:**
- Elasticsearch update issues, connection failures, query/index errors, integration, compatibility.

**Ask (required):**
- Elasticsearch version + deployment topology (single node/cluster).
- Error messages, recent updates, plugin list (if applicable).
- What operation fails: query vs indexing vs integration.

**Actions (internal):**
- Check cluster health, indexing pipeline, compatibility with plugins.
- Provide troubleshooting plan and relevant docs/sample configs.
- Escalate for intermittent/unexplained failures with focused investigation.

**Customer output must include:**
- Required-info checklist + first troubleshooting steps.
- What the team will check next + follow-up plan.

## Stage G — Hardware sizing & performance recommendations
### IT-G1 Minimum/recommended hardware specs
**Trigger:**
- Requests for hardware requirements or sizing guidance.

**Ask (recommended):**
- Workload type (dev/test/prod), user volume, data size, latency expectations.
- Current hardware specs (CPU/RAM/storage) and deployment model.

**Rules:**
- Provide tiered guidance: minimum vs recommended vs production.
- Explain trade-offs (SSD benefit, RAM for caching, CPU for concurrency).
- If below minimum: warn about bottlenecks and advise upgrades.

**Customer output must include:**
- A tiered spec table (light/standard/heavy).
- What specs matter most for their workload.

## Stage H — Security incidents & compliance-driven hardening
### IT-H1 Data breach / unauthorized access / vulnerability report
**Trigger:**
- Reported data breach, unauthorized access, security vulnerability.

**Ask (required, minimal):**
- Time of incident, affected systems, suspected access path, actions already taken.
- Types of data involved (high-level only).

**Actions (internal):**
- Initiate incident response, containment (isolation, credential resets, patching).
- Coordinate compliance steps (GDPR/HIPAA etc.) with security/legal.
- For large-scale incidents: crisis management escalation.

**Customer output must include:**
- Incident acknowledgement and immediate safety steps (non-sensitive).
- What info is needed next.
- Next update cadence / escalation notice.

### IT-H2 Medical data security enhancements (hardening request)
**Trigger:**
- Requests stronger protection for medical data, compliance support, security gaps.

**Ask (recommended):**
- Data type, deployment model, access patterns, current controls.

**Rules:**
- Recommend framework: encryption, access control, audit logs, MFA, monitoring.
- Offer security assessment / consulting if needed.

**Customer output must include:**
- High-level hardening plan + compliance checklist direction.
- Next steps for assessment and implementation.

## Stage I — Investment analytics tool issues (only if this is your supported product)
### IT-I1 Incorrect metrics/forecasts/model configuration problems
**Trigger:**
- Inconsistent analytics, inaccurate forecasts, optimization-model issues.

**Ask (required):**
- What metric/output is wrong + sample timeframe + data source(s).
- Model assumptions/parameters (risk level, horizon) if applicable.

**Rules:**
- Validate data ingestion integrity first, then model parameters/assumptions.
- Do not give investment advice; focus on tool correctness and configuration.

**Customer output must include:**
- What will be validated (data vs model vs configuration).
- What inputs are needed from the user.
- Next steps and escalation path if accuracy cannot be restored.



---
doc_id: security-policy
title: Security Policy
version: 2025-12-23
---

# Security Policy

## Constants (Single source of truth)
- SECURITY_FIRST: Treat suspected compromise as urgent; prioritize containment and escalation.
- NO_SECRETS: Never ask for passwords, full MFA codes, or full API keys; request masked identifiers only.
- EVIDENCE_PRESERVATION: Preserve evidence (headers/logs/screenshots) and avoid destructive actions unless instructed by Security.
- APPROVED_CHANNELS_ONLY: Use company-approved reporting channels for phishing and incidents.

## Stage A — MFA setup and troubleshooting

### SEC-A1 MFA enablement (standard setup)
**Trigger:**
- User asks how to enable MFA for a system (VPN, cloud storage, HR portal, project tools, knowledge base, analytics, etc.).

**Ask (minimal):**
- Which system/app is MFA being enabled for?
- Preferred method (TOTP app / SMS / email / hardware token), if user has a preference.

**Rules:**
- Provide step-by-step MFA setup guidance for the specific system.
- Explain supported methods (TOTP, SMS, email, hardware tokens) and required prerequisites.
- Remind user to store backup/recovery codes securely and use a strong password.

**Customer output must include:**
- Setup steps tailored to the requested system.
- Supported MFA methods.
- Backup code guidance and safety reminders.

### SEC-A2 MFA troubleshooting (codes not working / not received / incompatibility)
**Trigger:**
- User cannot complete MFA setup, does not receive codes, or sees device/system incompatibility issues.

**Ask (required):**
- Device type + OS version.
- Auth method (TOTP/SMS/email/token) and authenticator app name (if applicable).
- Error message + timestamp.
- Affected system/app name.

**Common fixes (safe actions):**
- For TOTP failures: verify automatic time/time-zone sync on the phone/device (time drift commonly breaks TOTP). [web:287]
- For SMS delivery issues: verify signal, avoid repeated rapid resends, and try an alternative method (TOTP/email) if available. [web:290]

**Escalate if:**
- Policy conflicts, legacy systems, MDM/group policy blocks, or compatibility matrix indicates unsupported configuration.
- User is locked out and cannot recover via backup codes.

**Customer output must include:**
- The most likely cause category (time sync vs delivery vs policy/compatibility).
- The next safe step to try.
- Clear escalation instructions if unresolved (include device/app/error details).

## Stage B — Phishing email handling and email security

### SEC-B1 Report a suspicious/phishing email (standard process)
**Trigger:**
- User reports a suspicious email or asks how to report phishing.

**Ask (minimal):**
- Whether the user clicked any link/opened attachments (yes/no).
- Email client type (optional, only if needed for instructions).

**Rules:**
- Use approved reporting method: email client “Report phishing/spam” OR forward to designated security mailbox/rule (per company policy).
- Tell user not to click links, not to open attachments, and to retain evidence (headers/body/attachments) for investigation.

**Customer output must include:**
- Exact reporting steps.
- Safety precautions (do not interact further; preserve evidence).

### SEC-B2 Phishing bypass / misrouting / wrongly marked safe
**Trigger:**
- Phishing bypassed filtering, was marked safe, or was forwarded externally.

**Ask (required):**
- Time, recipients, subject, sender, and any forwarding targets.
- Whether anyone interacted with the email (clicked, opened attachment, entered credentials).

**Actions (internal):**
- Immediate escalation to Security for investigation.
- Update filtering rules/blocklists/content policies as needed.

**Customer output must include:**
- Immediate containment guidance (stop interacting; report via approved channel).
- Confirmation that Security will investigate and follow up.

## Stage C — Workstation and endpoint security alerts

### SEC-C1 Endpoint security alerts / non-compliance / hardening issues
**Trigger:**
- Antivirus/DLP/EDR alerts, encryption/firewall control issues, device marked non-compliant, login anomalies after hardening guidance.

**Ask (required):**
- Device type + OS version.
- Security tool name/version (if known).
- Exact alert/error text + timestamp.
- Recent changes (updates, newly installed software).
- Whether baseline workstation hardening was completed (per internal guide).

**Rules:**
- Check MDM/domain policy deployment status, policy conflicts, and permissions.
- Review endpoint logs/update logs/security platform alerts.
- For intermittent DLP/EDR issues: collect logs and (if needed) traffic captures for deeper analysis.

**Escalate if:**
- Cannot remediate remotely, suspected defect, or repeated policy failures.
- Any sign of active compromise or suspicious access → treat as incident (SECURITY_FIRST).

**Customer output must include:**
- What was identified (high-level), what was remediated, and next recommendations.
- What evidence is needed next if unresolved.
- Confirmation that the incident is recorded for audit (internal).



---
doc_id: account-policy
title: Account & Access Management Policy
version: 2025-12-23
---

# Account & Access Management Policy

## Constants (Single source of truth)
- LEAST_PRIVILEGE: Grant users only the access needed to do their job, and avoid over-privileged permissions.
- NO_SECRETS: Never ask for passwords, MFA codes, or full API keys/tokens; request masked identifiers only.
- APPROVAL_REQUIRED: Any access grant/change must have the required approver (manager/system owner) per internal access control matrix.
- SELF_SERVICE_FIRST: For password/login issues, guide users to self-service reset first when available; escalate only if self-service fails.
- TRACEABILITY: Every access request must include requester identity, target system/resource, requested permission level, and approver for auditability.

## Stage A — Access requests (new access / permission changes)

### AC-A1 Provisioning / permission change request
**Trigger:**
- Requesting new access or changes to existing permissions (Email, Slack, SFDC, Jira, Dropbox, Google Drive, GitHub, Zoom host, etc.).

**Ask (required):**
- Requester name + company email.
- Target system(s) and exact resource scope (e.g., specific Slack channel, Dropbox folder).
- Requested permission level (read-only / edit / admin).
- Approver identity and proof of approval (manager/system owner).

**Rules:**
- Validate against the internal access control matrix and LEAST_PRIVILEGE.
- If compliant and approved: provision/update account or add user to correct group/role.
- If missing approval or non-compliant request: escalate for manual review/approval.

**Special cases:**
- New hire / role change: confirm onboarding or role-change process completed and record the approver.

**Customer output must include:**
- A confirmation of what was requested (systems + permission level).
- That the request is submitted per company policy and updates will be sent via email/system notification.
- Any missing required items (e.g., approver) as ONE clear request.

## Stage B — Account configuration (self-service / setup guidance)

### AC-B1 Password reset / login failure
**Trigger:**
- Forgotten password, login failure, account locked.

**Ask (minimal):**
- Which system/app is affected?
- Any error message (copy/paste) and timestamp.

**Rules:**
- Provide self-service password reset steps (SSO portal or “Forgot password” page) where applicable.
- If self-service fails: escalate to the account administrator/IdP team with error details.

**Customer output must include:**
- Short self-service steps.
- Link/path to the official reset flow (if you have one).
- What to provide if it fails (error + timestamp).

### AC-B2 Email / calendar / MFA / mobile device setup
**Trigger:**
- Questions about configuring accounts (email, calendar, MFA, mobile mail setup, etc.).

**Ask (recommended):**
- System/app name and device/platform (iOS/Android/Windows/macOS).
- Whether the user is using SSO/MFA and what method.

**Rules:**
- Provide high-level setup steps and link to detailed internal/external guides.
- If MFA is the core issue, route to the Security/MFA policy (avoid duplication).

**Customer output must include:**
- Minimal setup steps + where to find the full guide.
- Clear next step if the problem persists (contact support with details).

## Stage C — Provisioning issues (“I should have access but I don’t”)

### AC-C1 Access missing or not applied
**Trigger:**
- User reports expected access is missing or permissions aren’t applied.

**Ask (required):**
- Screenshot of the error (if possible), timestamp, and what access they expected.
- The request reference (ticket/request ID) if available.
- Approver information (if relevant).

**Rules:**
- Check for missing approvals, group sync delays, or incomplete provisioning.
- Escalate to system admin / IdP team if required.

**Customer output must include:**
- Confirmation that access/provisioning is being investigated.
- What additional info is needed (if any).
- Which team will follow up if escalation is required.



---
doc_id: billing-payments-policy
title: Billing & Payments Policy
version: 2025-12-23
---

# Billing & Payments Policy

## Constants (Single source of truth)
- NO_MONEY_CHANGES_BY_BOT: The bot must not promise refunds, credits, reversals, or billing adjustments; those require billing/finance workflows.
- NO_SECRETS: Never ask for full card numbers, CVV, passwords, or full bank details. Use masked info only.
- RECEIPT_REQUIRED: Billing investigations require a stable reference (invoice number, transaction ID, or account ID).
- ESCALATE_HIGH_RISK: Disputes, unauthorized charges, duplicate charges, or “wrong amount” are treated as high-risk and should be escalated.
- CLEAR_DISCLOSURE: Any extra fees must be disclosed before confirmation, and acceptance must be explicit.

> This document is structured to support header-based chunking (`##/###`) for RAG retrieval. [web:153]

## Stage A — Payment methods and subscription cycles

### BP-A1 Accepted payment methods
**Trigger:**
- User asks about accepted payment methods.

**Answer (policy):**
- Supported methods: credit cards (Visa/Mastercard/Amex), bank transfer, PayPal.

**Ask (only if needed):**
- Which country/region and which plan the user is trying to pay for (if methods vary).
- Whether this is a one-time payment or subscription renewal.

**Rules:**
- If user requests non-standard methods (checks, other services): require manual feasibility review (do not confirm availability).
- If payment fails: advise user to verify payment details, available balance/limits, and contact their bank/payment provider.

**Customer output must include:**
- Supported methods list.
- Next steps for non-standard method requests (manual review).
- Basic payment failure checklist (non-sensitive).

### BP-A2 Billing plans and subscription cycles
**Trigger:**
- User asks about billing plans, subscription cycles, discounts.

**Answer (policy):**
- Subscription cycles: monthly and annual.
- Longer commitments may qualify for discounts/special offers (do not promise; subject to eligibility/approval).

**Ask (recommended):**
- Desired cycle (monthly vs annual), approximate seats/users, and required modules (if relevant).

**Rules:**
- Custom plans may exist but must be recorded in the system and confirmed by sales/billing before considered active.

**Customer output must include:**
- Available cycles.
- A neutral statement about discounts (if eligible / subject to approval).
- Next step to confirm a custom plan (billing/sales follow-up).

## Stage B — Billing discrepancies and invoice issues (high-risk)

### BP-B1 Billing discrepancy / invoice dispute / duplicate charge
**Trigger:**
- User reports billing errors, duplicate charges, incorrect invoice, or discrepancies.

**Ask (required):**
- Invoice number or transaction ID.
- Account identifier (email/company) and billing period.
- Discrepancy description (what is wrong), affected amount(s), date(s).
- Screenshot of the invoice/statement with sensitive data masked (optional but helpful).

**Rules (internal handling):**
- Verify via billing systems/payment gateway logs and customer payment history.
- Compare invoice data to billing history.
- If error confirmed: corrected invoice and/or billing adjustment must be done by billing/finance workflow (NO_MONEY_CHANGES_BY_BOT).
- Record investigation outcome for auditability.

**Escalate:**
- Any suspected unauthorized charge, duplicate charge, “charged twice”, “wrong amount”, dispute/chargeback mention → escalate to billing/finance immediately (ESCALATE_HIGH_RISK).

**Customer output must include:**
- Confirmation of receipt of the dispute and what info is being reviewed.
- The single most important missing identifier (if any).
- Clear expectation: billing/finance will follow up after review (no promises of outcome).

## Stage C — Additional fees and extra costs (disclosure)

### BP-C1 Extra fees / add-on charges
**Trigger:**
- User asks about service pricing or potential additional charges.

**Ask (recommended):**
- Which plan/module and what feature/service they want (premium support, custom solution, upgrade, etc.).

**Rules:**
- Extra fee items and amounts must be documented in pricing materials or internal documentation.
- Before confirming a service/subscription: clearly disclose extra fees and obtain explicit acceptance.
- If customer declines: offer standard options or remove custom add-ons.

**Customer output must include:**
- Applicable fee items and amounts (or “requires review” if not published).
- Confirmation that fees are optional/conditional and require acceptance.
- Next steps if they do not accept (standard plan / remove add-ons / cancel request).



---
doc_id: general-inquiry-policy
title: General Inquiry Policy
version: 2025-12-23
---

# General Inquiry Policy

## Constants (Single source of truth)
- ROUTE_IF_SPECIALIZED: If the question clearly matches Account / Billing / IT / Sales / Security / Returns, route to that policy instead of answering here.
- USE_OFFICIAL_INFO_ONLY: Use only approved/official descriptions for org/process/policy statements; avoid speculation.
- NO_COMMIT_DATES: Do not promise specific completion dates; use neutral timelines (“after verification”, “once confirmed”).
- NO_PROFESSIONAL_ADVICE: No legal, compliance, medical, or investment advice; provide general information and recommend qualified teams.
- REQUEST_SCOPE_FIRST: If the request is broad or unclear, ask ONE clarifying question to define scope.

## Stage A — Org structure & process info

### GI-A1 Org structure / responsibility / process / SLA info request
**Trigger:**
- Requests about org structure, department responsibilities, key contacts.
- Requests to update internal records (R&R, process descriptions, SLAs, constraints).

**Ask (required):**
- Which organization/team/product line does this apply to?
- What exact field(s) need to be added/updated (org chart, contact list, process doc, SLA, constraints)?
- Supporting material (org chart, contact list, doc link/file), if available.

**Rules:**
- If the knowledge base already contains the info, respond with the current official version and note it may change over time.
- If confirmation is required, explain it must be verified with the relevant owner team(s); do not give a fixed completion date.

**Escalate if:**
- The requester asks for authoritative changes without an approver/owner or required evidence.

**Customer output must include:**
- Summary of what will be updated/verified.
- What is currently known (if any).
- What materials are required.
- Neutral timeline wording (“we’ll follow up once confirmed”).

## Stage B — General usage questions (non-troubleshooting)

### GI-B1 “How do I use this?” / unclear instructions
**Trigger:**
- “Instructions are unclear”, “operation is confusing”, “service details are not clear”.
- General feature/use-case/delivery-model questions.

**Ask (required, one question max if unclear):**
- Is the user trying to troubleshoot a malfunction, or learn standard usage?

**Rules:**
- If covered by docs: provide a brief overview and point to the detailed guide.
- If it becomes solution design/strategy: provide high-level principles and recommend arranging a deeper discussion with the appropriate team.

**Customer output must include:**
- 1–2 sentences confirming understanding.
- Concise steps/overview + documentation pointer.
- If advisory: recommend follow-up discussion and avoid prescriptive plans.

## Stage C — Suggestions & enhancement requests (non-critical)

### GI-C1 New feature / new integration / UI improvement suggestion
**Trigger:**
- Requests for new integrations, UI optimization, onboarding updates, feature enhancements.

**Ask (required):**
- Use case + expected benefit + who is impacted.
- Any constraints (deadline preference is optional but not promised).

**Rules:**
- Acknowledge and record the request for product/engineering evaluation.
- Do not commit to release dates, delivery timelines, or implementation details.

**Customer output must include:**
- Whether it appears “already supported” or “new request” (if known).
- Confirmation it will be reviewed and updates will be shared via official channels.
- Clear statement of no committed ETA.

## Stage D — HR operations (handled under General)

### GI-D1 HR onboarding/training/offboarding questions
**Trigger:**
- Questions about onboarding processes, training options, offboarding steps, training resource gaps.

**Ask (recommended):**
- Target roles/team, required tools, preferred training format (self-paced / live / webinar), target timing window.

**Rules:**
- Provide available onboarding/training formats and what’s supported.
- If the request implies program changes (new training program, expanded scope), log it as an improvement request for HR owners.

**Customer output must include:**
- Overview of available options and next step to enroll/schedule.
- What details are needed to tailor training.

### GI-D2 HR policies & benefits clarification
**Trigger:**
- Questions about remote/flexible work policies, employee benefits, or inconsistent policy answers.

**Ask (required):**
- Country/region, department, and role type (eligibility may vary).

**Rules:**
- Provide the currently effective policy wording and link to the official source where available.
- If inconsistencies are reported repeatedly, escalate to the HR policy owner for clarification and documentation updates.

**Customer output must include:**
- Concise, unified explanation based on current policy.
- Where to find the official policy source.
- Escalation note if ambiguity exists.

### GI-D3 Org role overlap & employee engagement concerns
**Trigger:**
- Reports of unclear responsibilities after re-org, role overlap, reduced engagement, or communication exclusion.

**Ask (recommended):**
- Affected teams/roles, examples of overlap, and impact.

**Rules:**
- Recommend follow-up with management/HR to clarify responsibilities and communication routines.
- Log as an “organizational/process improvement” item for tracking.

**Customer output must include:**
- Confirmation the concern is recorded.
- Suggested next steps (alignment meeting / HR follow-up).
- A neutral feedback timeline (no fixed dates).

### GI-D4 HR documents / handbook updates / translation issues
**Trigger:**
- Requests to update handbooks; reports translation errors (including machine-translation inaccuracies).

**Ask (required):**
- Document type, language(s), and specific error examples/sections.

**Rules:**
- Submit revision request to HR content owners and localization/translation owners.
- Do not treat machine translation output as final.

**Customer output must include:**
- Confirmation the revision request is logged.
- What examples are needed.
- Neutral follow-up language (“we’ll share the updated link once available”).
