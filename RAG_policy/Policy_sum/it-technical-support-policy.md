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
