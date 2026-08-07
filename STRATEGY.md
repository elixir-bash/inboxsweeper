# Strategy — a house of free, private, everyday tools

North-star for the "nuggets" venture: small, high-value utilities that solve everyday
annoyances, given away free, kept radically private. Mail cleanup is the flagship.

## 1. Brand architecture
- **Umbrella brand** = the promise: *free, private, no-signup tools for everyday problems.*
  (Working directions: Kindware / GoodBits / Everyday / Nuggets.) Decide this first — every
  new nugget markets the last.
- **Nuggets** = individual tools under the umbrella. #1 = the mail cleaner (working title
  **InboxSweeper**). Future: duplicate-file finder, subscription tracker, photo declutter, etc.

## 2. The nugget template (leverage)
Every nugget ships from one template so a new tool takes days, not weeks, and they all feel
identical:
- Shared **design system** (dark UI, extracted to a CSS kit)
- Shared **local web-app shell** (the `serve` pattern)
- Shared **backend** (this repo's `worker/` — analytics + feedback)
- Shared **first-run consent**, README skeleton, landing-page template, installer build
- A **hub site** listing all nuggets.

## 3. UX principles (minimalist, all ages)
1. One screen, one primary action. Plain words ("Clean my inbox," not "Execute IMAP sweep").
2. Guided, not configured — smart defaults; advanced hidden.
3. Show, then confirm — always preview counts before acting; always reversible.
4. Accessible — large text, high contrast, keyboard-first, runs on old hardware.
5. Zero-to-value in <60s.

## 4. Privacy stance (the moat)
Everything runs **on the user's device**; email content and identity never leave. This is the
one thing paid competitors (MailMop, Clean Email) can't match. Guard it obsessively — it's the
whole brand.

## 5. Anonymous analytics — with the honest caveat
Analytics means *something* leaves the device, which is in tension with the privacy pitch.
Resolve with precision + transparency:
- **Capture (anonymous only):** random install UUID, tool + version, OS, and counters (runs,
  emails cleaned, unsubscribes, provider). Public aggregate → a live "N emails swept for M
  people" counter = social proof.
- **Never capture:** addresses, senders, subjects, content, anything identifying.
- **Consent:** first-run one-line prompt + `NO_TELEMETRY=1` env + UI toggle. Precise message:
  *"Your email content and identity never leave your device; we count anonymous usage totals,
  which you can turn off."*
- **Stack:** one Cloudflare Worker + KV (free tier) — see `worker/`. No vendor, no cookies.

## 6. Feedback (in-git, we can reply)
- **giscus** inline comments → GitHub Discussions (needs GitHub sign-in).
- **Login-free path** for non-technical users: site form → the same Worker → opens a GitHub
  Issue via bot token. Everything lands in git; triage/reply via `gh`.

## 7. Rollout
1. Extract the shared kit (design system + shell + worker + templates) from InboxSweeper.
2. Ship InboxSweeper v1 with consent + live counter.
3. Stand up the hub site.
4. Template nugget #2 to prove the pipeline is days-fast.
