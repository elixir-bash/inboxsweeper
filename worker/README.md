# InboxSweeper backend (Cloudflare Worker)

Shared, free-tier backend for the nuggets: **anonymous usage counters** + **login-free
feedback → GitHub Issues**. No database vendor, no cookies.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/stats` | Live totals for the landing page: `{users, emails, gb, unsubs}` |
| `POST` | `/event` | Anonymous counts from the tool (`{uid, emails, mb, unsubs}`) — counts only |
| `POST` | `/feedback` | `{message, contact?, tool?}` → opens a GitHub Issue (rate-limited, honeypot) |

## Deploy (one time, ~5 min)
Requires a free Cloudflare account and Node.

```bash
npm i -g wrangler
wrangler login

cd worker
wrangler kv namespace create STATS      # copy the id → paste into wrangler.toml
wrangler secret put GH_TOKEN            # paste a GitHub PAT with public_repo (issues) scope
wrangler deploy
```

`wrangler deploy` prints your Worker URL, e.g. `https://inboxsweeper-backend.<you>.workers.dev`.

## Wire it up
1. **Landing page** (`docs/index.html`): set `const WORKER_URL = "https://…workers.dev"` — this
   turns on the live counter and the feedback form.
2. **The tool**: point telemetry at it — `export INBOXSWEEPER_STATS_URL="https://…workers.dev"`.
   (Telemetry is **off** until this is set. Disable always with `INBOXSWEEPER_NO_TELEMETRY=1`.)

## Privacy
`/event` records counters only (installs, emails cleaned, MB freed, unsubscribes). It never
receives addresses, senders, subjects, or content — the client doesn't send them. The install
`uid` is a random UUID with no link to identity.
