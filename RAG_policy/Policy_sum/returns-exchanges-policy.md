---
doc_id: returns-exchanges-policy
title: Returns & Exchanges Policy
version: 2025-12-23
---

# Returns & Exchanges Policy

## Constants (Single source of truth)
- RETURN_WINDOW_DAYS: 30 days from receipt.  # Generic return window (most items)
- REFUND_SLA_AFTER_RECEIPT: 5–7 business days after warehouse receives item.  # Refund processing time
- EXCHANGE_SLA_AFTER_RECEIPT: 5–7 business days after warehouse receives item. # Exchange processing time
- HUMAN_RESPONSE_SLA: 1–2 business days (only when escalated).

> Note: Always express timelines with a trigger point (“after warehouse receives the item”).
> Do not promise exact dates.

---

## Stage A — General return window (no order info)

### RE-A0 Generic return window
**Trigger:**  
Customer only asks about the general return timeframe (e.g., “how long to return”, “how many days for return”, “how long do refunds/exchanges take”) and does NOT provide order details.

**Ask (optional):**
- If the customer insists on “just the policy”, do NOT require an order number.
- If they later want to confirm a specific order, then ask for order number + purchase date.

**Rule:**
- Standard return window is RETURN_WINDOW_DAYS from the date the customer receives the item.
- Items must meet standard return conditions: unused, in resellable condition, with original packaging and accessories where applicable.
- After the warehouse receives and accepts the return, refunds are usually processed within REFUND_SLA_AFTER_RECEIPT and exchanges within EXCHANGE_SLA_AFTER_RECEIPT.

**Customer output must include:**
- A clear sentence about the generic window, including conditions.  
  - e.g., “In general, items can be returned within RETURN_WINDOW_DAYS from the day you receive them, as long as they are unused and meet the standard return conditions.”
- A clear sentence about processing time after receipt.  
  - e.g., “Once our warehouse receives and checks the returned item, refunds or exchanges are usually completed within REFUND_SLA_AFTER_RECEIPT / EXCHANGE_SLA_AFTER_RECEIPT.”
- A soft offer to check a specific order if the customer shares their order number.

---

## Stage A — Customer has NOT initiated a return

### RE-A1 Standard return inquiry
**Trigger:**  
Customer asks how to return/refund, detailed conditions, shipping fee, OR asks about eligibility for a specific order (often with order details).

**Ask (required):**
- Order number, purchase/receipt date, product name.
- Condition: unused + original packaging + proof of purchase (if required).

**Rule:**
- Start from the generic rule in RE-A0 (RETURN_WINDOW_DAYS + standard conditions).
- Most items must be returned within RETURN_WINDOW_DAYS.
- If NOT defect/incorrect shipment: customer usually pays return shipping; restocking fee may apply (if policy says so).

**Exceptions:**
- Clearance/special products: eligibility depends on item policy → escalate if unclear.

**Customer output must include:**
- Whether they appear eligible (based on info provided).
- How to initiate in the portal (do not invent a return address in chat).
- Shipping/responsibility & possible fees (neutral wording if uncertain).
- Refund timeline: REFUND_SLA_AFTER_RECEIPT (no tighter promise).

---

## Stage A — Customer wants an exchange

### RE-A2 Exchange request
**Trigger:**  
Customer explicitly requests an exchange (size/model) or replacement of a defective item.

**Ask (required):**
- Order number, product name, purchase date.
- Serial number (if applicable).
- Reason: defect vs incorrect shipment vs preference.

**Eligibility:**
- Within RETURN_WINDOW_DAYS.
- Original packaging + accessories (if required).

**Shipping wording:**
- If responsibility is not explicit: use neutral wording such as “subject to review” (avoid firm commitments).

**Escalate if:**
- Technical defect needs troubleshooting details.
- Multi-item or ambiguous eligibility.

**Customer output must include:**
- Eligibility summary.
- What must be returned.
- Shipping fee wording (who likely pays, or that it is subject to review).
- Exchange timeline: EXCHANGE_SLA_AFTER_RECEIPT.

---

## Stage B — Customer initiated return but is blocked / needs RMA / label

### RE-B1 Portal/RMA handling
**Trigger:**  
Customer asks about return address / next step / portal issues / needs RMA.

**Ask (required):**
- Order number OR return reference/RMA.
- Where they are blocked (login, missing email, unclear RMA, etc.).
- Error screenshots/messages (if any).

**Process steps (explain clearly):**
1) Submit request in the online portal.  
2) System reviews and generates an RMA (if applicable).  
3) Return address and label are provided via portal/email.  
4) Warehouse receives item → refund or exchange is triggered.

**Exception handling:**
- Portal errors → create an internal ticket.
- Provide a backup option (e.g., request label via email) but do not guarantee the bot can issue it.

**Customer output must include:**
- Exactly where to find the RMA/label.
- The next step to unblock the return.

---

## Stage C — Status, delays, “have you received it?”

### RE-C1 Status & delay inquiry
**Trigger:**  
“I sent it but no updates”, “how long until refund”, “did you receive it”.

**Ask (required):**
- Order/return number, shipment date, tracking number.

**Bot logic:**
- If real-time status exists: show received / in transit / processing.
- If status cannot be retrieved OR it exceeds REFUND_SLA_AFTER_RECEIPT → escalate.

**Customer communication:**
- Apologize + neutral assurance.
- Never fabricate dates.

**Escalation output (if escalated):**
- Human follow-up within HUMAN_RESPONSE_SLA.

---

## Stage D — Refund amount / fee disputes

### RE-D1 Amount dispute
**Trigger:**  
Customer disputes refund amount, shipping/restocking fee deduction.

**Ask (required):**
- Order number, original paid amount, expected refund amount + reason.

**Rule:**
- Explain preliminary calculation logic only.
- Do not adjust money in the bot flow.

**Escalate:**
- All monetary disputes → finance / second-line review.
