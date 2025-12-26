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
