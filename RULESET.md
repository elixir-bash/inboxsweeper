# Email Hygiene Ruleset (first principles)

The policy this tool follows. Goal: kill noise, never lose anything that matters, never make
yourself a bigger spam target.

## The 3 outcomes for any bulk email
1. **Unsubscribe** — a legitimate sender you recognize / once opted into. Stops future mail at
   the source. Safe *only* for recognized senders.
2. **Report spam / block** — a sender you never signed up with or don't recognize.
   **Do NOT unsubscribe these** — clicking confirms your address is live and invites more, and
   the link itself can be a phishing/malware trap. Marking spam is the correct signal.
3. **Keep** — transactional or personally valuable. Never bulk-touch.

> **Core rule: recognize it → unsubscribe. Don't recognize it → report spam. Never
> unsubscribe from something you don't remember signing up for.**

## First principles
1. **Clean by SENDER, not by category.** Gmail's "Updates" tab is full of *transactional* mail
   (receipts, orders, shipping, security). Category-wide deletes destroy real records.
2. **Deletion is reversible or it doesn't happen.** Bulk removal MOVES to Bin (30-day
   recovery). Never permanent-delete in bulk. Verify a sample before emptying.
3. **Unsubscribe method safety order: one-click (RFC 8058) > mailto > web link.**
   - *one-click* = background HTTP POST, no landing page — safest.
   - *mailto* = sends an email from you — safe, auditable.
   - *web link* = arbitrary URL → click only for **trusted** senders; never for unknown ones.
4. **Marketing ≠ transactional.** Unsubscribing from a promo list never stops receipts,
   confirmations, or security/account mail — those ride a separate stream.
5. **Automate the recurring, sweep the backlog once.** A sweep clears history; a **filter**
   stops the pattern forever. Do both.
6. **Aliases for the future.** Use `you+shopping@gmail.com` / `you+news@gmail.com` at signup so
   a whole class can be filtered or removed later without collateral damage.

## PROTECT — never bulk-delete or auto-unsubscribe
- **Financial:** banks, brokerages, investment, insurance, credit bureaus, lenders.
- **Security:** password managers, 2FA, sign-in alerts, password resets.
- **Government & tax:** `*.gov`, tax software, immigration, DMV, city/utility notices.
- **Transactional:** receipts, invoices, orders, shipping, bookings, reservations, tickets, statements.
- **Medical / legal.**
- **Personal:** mail from real people and lists you're active on.
- **Work:** employer domains and dev/service accounts you use.

## DELETE + UNSUBSCRIBE — safe targets (recognized senders)
Retail & promos, food delivery, travel/hotel marketing, job-board alerts, real-estate listing
alerts, newsletters/digests, event/webinar blasts, survey requests, "deals" mail.

## KEEP-BY-DEFAULT — value judgments (ask, don't assume)
Community / religious / cultural org newsletters, hobby/interest newsletters, alumni,
causes/donations. Noise to a filter, meaningful to a person — leave unless the owner says so.

## Operating procedure
1. `counts` → find where the mass is.
2. `profile` → rank the noisy senders.
3. Classify each sender: PROTECT / DELETE / KEEP-BY-DEFAULT.
4. `sweep` (dry-run → `--yes`) the DELETE set to Bin. Verify, then empty if happy.
5. `unsub-list` → `unsub-run` the recognized DELETE senders (one-click/mailto only).
6. Unrecognized/spammy: **report spam**, don't unsubscribe.
7. Add Gmail **filters** for top recurring offenders.
8. Re-run quarterly.
