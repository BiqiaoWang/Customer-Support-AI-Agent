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
