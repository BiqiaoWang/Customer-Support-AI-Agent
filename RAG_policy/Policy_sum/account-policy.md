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
