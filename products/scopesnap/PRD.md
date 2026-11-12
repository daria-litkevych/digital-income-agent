# ScopeSnap — Product Requirements (MVP)

**Status:** Prototype hypothesis; not validated.  
**Version:** 0.1  
**Audience:** Freelancers, consultants, designers, developers and other independent service providers.

## Problem

A client requests work that may be outside the agreed scope. The freelancer must decide whether it is included, estimate the extra effort and price, explain the impact, and get clear approval before doing the work. In practice, small requests can be handled informally in chat, creating ambiguity and unpaid work.

This product does not determine legal scope or interpret contracts. It helps the freelancer prepare a clear commercial summary of a change they have already decided is additional.

## Core promise

**Turn an extra client request into a clear, priced change summary in about a minute.**

## Primary user story

As a freelancer, when a client asks for additional work, I want to enter the request, effort and price, then generate a professional summary I can send to the client before starting, so that both sides understand the extra cost and timeline.

## MVP requirements

1. No account, signup or backend.
2. Responsive single-page interface.
3. Inputs: freelancer/business name (optional), client/project (optional), original scope reference, requested change, additional hours, hourly rate, extra costs, revised delivery impact.
4. Calculate additional labour cost, extra costs and total additional price.
5. Generate a readable client-facing change summary.
6. Copy summary to clipboard.
7. Print / save as PDF using browser print.
8. Include explicit approval status placeholder; no e-signature or automated sending.
9. Clear privacy note: entered data stays in the current browser session and is not uploaded or stored by this MVP.
10. No legal advice, enforceability or tax treatment claims.

## Out of scope

- Uploading or analysing contracts.
- AI judgement about whether a request is within scope.
- E-signature, payment, invoice generation or email sending.
- Client portal, accounts, cloud sync or multi-user collaboration.
- VAT/tax calculations or legal clauses.

## UX principles

- Open and use immediately.
- One screen, short labels, sensible defaults.
- Show the calculation transparently.
- Make the client-ready output the main result.
- Avoid forcing the user to configure a project before creating a change.

## Acceptance criteria

- Empty/invalid numeric inputs are handled safely.
- Negative hours/rates/costs are rejected or treated as zero with clear feedback.
- Totals update when inputs change.
- Currency formatting is clear and can be changed.
- Copy action copies only the generated summary.
- Print layout is readable on paper/PDF.
- Layout works on mobile widths.
- No network request, account, external library or persistent data storage is required.

## Validation plan

Run 5–8 moderated usability sessions with freelancers. Observe completion without explaining the UI. Record completion time, confusion points, whether the summary would be sent, current alternatives and willingness to pay. This sample is directional, not statistically representative.

## Commercial hypothesis

Free basic calculator; potential paid add-on could be a branded export, reusable scope/change templates or saved local presets. Do not implement paid tiers until willingness to pay is tested.
