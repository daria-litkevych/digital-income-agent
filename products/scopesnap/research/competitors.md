# ScopeSnap — Competitor and substitute review

**Reviewed:** 12 November 2026. **Status:** desk research only; no interviews, usage tests, verified sales or willingness-to-pay evidence.

## Decision

The current ScopeSnap prototype is a browser-only hours/rate/expense calculator that produces a copyable change summary. Useful as a demonstration, but **not yet a defensible paid product**. Freelancer platforms already bundle proposals, contracts, forms, portals and invoices; free templates and email workflows are substitutes. A no-login approval link could be a stronger hypothesis, but needs backend, secure links and data handling. Do not build that complexity until the workflow is better evidenced.

## Competitors and substitutes

| Product | Public offer checked | Implication |
|---|---|---|
| Dubsado | Starter $35/month or $335/year; Premier $55/month or $525/year. Invoicing, forms and client portals; Premier adds public proposals and automation. [Official pricing](https://www.dubsado.com/pricing) | Broad client workflow; ScopeSnap must be much simpler or solve a distinct gap. |
| Bonsai | Basic $9/user/month annually; Essentials $19/user/month annually includes invoices, payments, proposals, contracts, forms, scheduling and client portal. [Official pricing](https://www.hellobonsai.com/pricing) | Direct overlap; a calculator alone is weak for users already paying for Bonsai. |
| HoneyBook | Offers templates, contracts/e-signatures, invoices, proposals, file tracking and client workflows. [Official pricing/features](https://www.honeybook.com/pricing) | Another broad substitute; verify exact current tier prices before price comparisons. |
| ScopeYes | Dedicated scope/change-request workflow: define scope, create changes, show cost/timeline impact and request approval. [Product guide](https://www.scopeyes.com/guides/client-change-request-template) | Confirms category competition; inspect real product depth and independent feedback. |
| ScopeDue | Free change-request template. [Template](https://scopedue.com/templates/change-request/freelance-change-request-template/) | Strong free substitute for a static template pack. |
| Email + contract clause | Freelancers describe sending written estimates and requesting approval before extra work. [Community discussion](https://www.reddit.com/r/webdev/comments/1r2o1mw/scope_creep_do_you_have_a_system_or_are_you_just/) | Product must remove real friction, not merely formalise a message. |

## First-hand community signals

1. A May 2026 freelancer describes repeated scope changes and disruptive client communication. [Discussion](https://www.reddit.com/r/freelance/comments/1to9m9h/nightmare_client_from_hell_please_help/) — **medium confidence** for existence of this pain in one case, not prevalence.
2. A March 2026 web developer discussion recommends a written change-request process and approval before starting extra work. [Discussion](https://www.reddit.com/r/webdev/comments/1r2o1mw/scope_creep_do_you_have_a_system_or_are_you_just/) — **medium confidence** for a current workaround; anecdotal.
3. An August 2026 post describes no-login links and milestone sign-off as more usable than asking clients to join Trello/Notion. [Discussion](https://www.reddit.com/r/freelancing/comments/1vqtwyj/quick-update-on-that-client-scope-creep-issue/) — **low confidence**: low engagement and potentially promotional/self-reported experiment.
4. An August 2026 post pitches a tool the author built for scope creep. [Discussion](https://www.reddit.com/r/freelancing/comments/1vlmog5/how_do_you_guys_deal_with_clients_who_keep_asking/) — **low confidence** as demand evidence; founder promotion, useful only for competitor discovery.
5. An October 2026 launch post describes ScopeYes and the same workflow. [Discussion](https://www.reddit.com/r/buildinpublic/comments/1wxkoyw/i_built_a_small_tool_to_solve_a_problem_i_kept/) — **low confidence** for demand; founder marketing, not independent review.

## What the evidence supports

- Some freelancers describe scope changes and unpaid extra work as real problems.
- Workarounds include written messages, contract clauses, proposals and milestone sign-off.
- Established platforms bundle much more complete client workflows.
- Avoiding client login friction is a plausible UX hypothesis.

## What it does not support

- Market size, population-level frequency or competitor sales.
- Willingness to pay for a separate calculator or template.
- That a no-login approval link is sufficiently differentiated or trusted.
- Commercial success based on competitor existence or launch posts.

## Product decision

**Keep ScopeSnap as a learning prototype; do not promote it as the chosen business yet.** Compare three shapes if it remains a finalist:

A. Current calculator + client-ready text — smallest, but easy to copy.  
B. Reusable change-request kit with message templates and worked examples — cheap, but free-substitute risk.  
C. Private no-login approval link with auditable change summary — stronger workflow hypothesis, but higher backend/security/support cost.

Before expanding, compare other B2C, B2B and prosumer opportunities. Any validation must measure actual workflow use, whether the summary is sent, current workaround and credible price acceptance. Complaints and compliments alone are not enough.
