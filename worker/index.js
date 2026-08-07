/**
 * InboxSweeper backend — shared Cloudflare Worker for the "nuggets" tools.
 *
 * Two jobs, no database vendor:
 *   1. Anonymous usage counters (KV)  → GET /stats returns the live totals for the site.
 *   2. Login-free feedback            → POST /feedback opens a GitHub Issue via a bot token.
 *
 * Bindings (see wrangler.toml):
 *   STATS     KV namespace (counters)
 *   GH_REPO   var, e.g. "elixir-bash/inboxsweeper"
 *   GH_TOKEN  secret, a GitHub PAT with `public_repo` (issues) scope
 *
 * Privacy: /event accepts counts only. Addresses, senders, subjects and content are never
 * sent by the client and are ignored if present.
 */

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", ...CORS } });

async function incr(env, key, by = 1) {
  const v = parseInt((await env.STATS.get(key)) || "0", 10) + by;
  await env.STATS.put(key, String(v));
  return v;
}

async function rateLimited(env, ip) {
  const key = "rl:" + ip;
  const n = parseInt((await env.STATS.get(key)) || "0", 10);
  if (n >= 5) return true;                       // max 5 feedback posts / minute / IP
  await env.STATS.put(key, String(n + 1), { expirationTtl: 60 });
  return false;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    // --- live totals for the landing page ---
    if (request.method === "GET" && url.pathname === "/stats") {
      const [users, emails, mb, unsubs] = await Promise.all(
        ["c:users", "c:emails", "c:mb", "c:unsubs"].map((k) => env.STATS.get(k))
      );
      return json({
        users: +users || 0,
        emails: +emails || 0,
        gb: Math.round(((+mb || 0) / 1024) * 10) / 10,
        unsubs: +unsubs || 0,
      });
    }

    // --- anonymous usage event from the tool ---
    if (request.method === "POST" && url.pathname === "/event") {
      const b = await request.json().catch(() => ({}));
      if (b.uid && !(await env.STATS.get("u:" + b.uid))) {
        await env.STATS.put("u:" + b.uid, "1");
        await incr(env, "c:users");
      }
      await incr(env, "c:runs");
      if (b.emails) await incr(env, "c:emails", Math.max(0, b.emails | 0));
      if (b.mb) await incr(env, "c:mb", Math.max(0, Math.round(b.mb)));
      if (b.unsubs) await incr(env, "c:unsubs", Math.max(0, b.unsubs | 0));
      return json({ ok: true });
    }

    // --- login-free feedback → GitHub Issue ---
    if (request.method === "POST" && url.pathname === "/feedback") {
      const ip = request.headers.get("CF-Connecting-IP") || "0";
      if (await rateLimited(env, ip)) return json({ error: "slow down a moment" }, 429);
      const b = await request.json().catch(() => ({}));
      if (b.website) return json({ ok: true });                 // honeypot: silently drop bots
      const message = (b.message || "").toString().slice(0, 5000).trim();
      if (message.length < 3) return json({ error: "message too short" }, 400);
      const contact = (b.contact || "").toString().slice(0, 200);
      const title = "Feedback: " + message.split("\n")[0].slice(0, 60);
      const body =
        message +
        (contact ? "\n\n— contact: " + contact : "") +
        "\n\n_(via site" + (b.tool ? ", tool: " + b.tool : "") + ")_";
      const r = await fetch("https://api.github.com/repos/" + env.GH_REPO + "/issues", {
        method: "POST",
        headers: {
          Authorization: "Bearer " + env.GH_TOKEN,
          Accept: "application/vnd.github+json",
          "User-Agent": "inboxsweeper-worker",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, body, labels: ["feedback", "from-site"] }),
      });
      if (!r.ok) return json({ error: "could not file feedback" }, 502);
      const issue = await r.json();
      return json({ ok: true, url: issue.html_url });
    }

    return json({ error: "not found" }, 404);
  },
};
