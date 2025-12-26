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
