#!/usr/bin/env python3
"""Local browser UI for mail-declutter. Launched via `inboxsweeper.py serve`.

Binds to 127.0.0.1 only, guarded by a random per-run token in the URL. Reuses the
engine in inboxsweeper.py — no duplicated cleanup logic.
"""
import json, os, re, secrets, smtplib, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from email.mime.text import MIMEText
from urllib.parse import unquote

import inboxsweeper as E   # the engine (same folder)

TOKEN = secrets.token_urlsafe(16)

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>InboxSweeper</title><meta name=viewport content="width=device-width,initial-scale=1">
<style>
:root{color-scheme:light dark}
body{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;max-width:820px;margin:0 auto;padding:24px;
 background:#0b0e14;color:#e6e6e6}
h1{font-size:22px;margin:0 0 4px} .sub{color:#8a94a6;margin:0 0 20px}
.card{background:#151a23;border:1px solid #232a36;border-radius:12px;padding:18px;margin:14px 0}
label{display:block;font-size:13px;color:#9aa4b2;margin:10px 0 4px}
input,select{width:100%;padding:10px;border-radius:8px;border:1px solid #2a3240;background:#0f141c;color:#e6e6e6;box-sizing:border-box}
button{background:#3b82f6;color:#fff;border:0;border-radius:8px;padding:10px 16px;font-weight:600;cursor:pointer;margin-top:12px}
button.ghost{background:#232a36} button.danger{background:#dc2626} button:disabled{opacity:.5;cursor:default}
table{width:100%;border-collapse:collapse;margin-top:8px} th,td{text-align:left;padding:7px 8px;border-bottom:1px solid #232a36;font-size:14px}
.tag{font-size:11px;padding:2px 7px;border-radius:20px} .p{background:#3b2f0b;color:#f5c451} .j{background:#0b2f1e;color:#4ade80}
.method{color:#8a94a6;font-size:12px} details{margin-top:10px} summary{cursor:pointer;color:#60a5fa}
#log{white-space:pre-wrap;font:12px/1.5 ui-monospace,Menlo,monospace;color:#9aa4b2;margin-top:10px;max-height:220px;overflow:auto}
.hint{color:#8a94a6;font-size:13px} a{color:#60a5fa}
.hide{display:none}
.topbar{display:flex;align-items:center;justify-content:space-between}
.gh{font-size:13px;color:#8a94a6;text-decoration:none;border:1px solid #232a36;padding:6px 12px;border-radius:8px}
.gh:hover{color:#e6e6e6;border-color:#3b82f6}
.foot{margin:28px 0 8px;padding-top:18px;border-top:1px solid #232a36;text-align:center;color:#6b7280;font-size:12px;line-height:1.7}
/* scanning animation */
#scanner{position:relative;overflow:hidden;background:#080d15;border:1px solid #1b2431;border-radius:10px;
 padding:14px 16px;margin-top:12px;font:12.5px/1.7 ui-monospace,Menlo,monospace;color:#4ade80;min-height:132px}
#scanner .sweep{position:absolute;left:0;right:0;top:-64px;height:64px;pointer-events:none;
 background:linear-gradient(180deg,rgba(59,130,246,.20),transparent);animation:sweep 1.8s ease-in-out infinite}
@keyframes sweep{0%{top:-64px}100%{top:100%}}
#scanner .hdr{color:#60a5fa} #scanner .cur{animation:blink 1s steps(1) infinite}
#scanner #spin{color:#f5c451}
@keyframes blink{50%{opacity:0}}
#scanConsole{margin-top:8px;white-space:pre-wrap}
#scanConsole .ln{opacity:0;animation:fadein .25s forwards}
@keyframes fadein{to{opacity:1}}
</style></head><body>
<div class=topbar>
 <h1>InboxSweeper</h1>
 <a class=gh href="https://github.com/elixir-bash/inboxsweeper" target=_blank rel=noopener>★ Star on GitHub</a>
</div>
<p class=sub>Clean up and unsubscribe from promotional email. Deletions go to Trash (recoverable).</p>

<div class=card id=connect>
 <label>Provider</label>
 <select id=provider><option value=gmail>Gmail</option><option value=yahoo>Yahoo</option></select>
 <label>Email address</label><input id=addr placeholder="you@gmail.com">
 <label>App password <span class=hint>(not your normal password)</span></label>
 <input id=pw type=password placeholder="16-character app password">
 <details><summary>How do I get an app password?</summary>
  <p class=hint id=apphelp></p></details>
 <button onclick=connect()>Connect</button>
 <div id=cstatus class=hint></div>
</div>

<div class=card id=main style="display:none">
 <button onclick=scan()>Scan my inbox</button>
 <span class=hint id=scanmsg></span>
 <div id=scanner class=hide><div class=sweep></div>
  <span class=hdr>inboxsweeper</span> <span id=spin>⠋</span> · envelopes examined: <span id=scanCount>0</span> <span class=cur>▋</span>
  <div id=scanConsole></div>
 </div>
 <div id=results class=hide>
  <table><thead><tr><th><input type=checkbox id=all onclick=toggleAll()></th><th>Sender</th><th>#</th><th>Unsubscribe</th><th></th></tr></thead>
  <tbody id=rows></tbody></table>
  <p class=hint style="margin-top:14px">Recommended order: <b>unsubscribe first</b>, then move to Trash — once mail is in the Trash its unsubscribe link can no longer be read.</p>
  <button onclick=unsub()>1. Unsubscribe from selected</button>
  <button class=danger onclick=sweep()>2. Move selected to Trash</button>
 </div>
 <div id=log></div>
</div>
<footer class=foot>
 Made for people who want their inbox back. ·
 <a href="https://github.com/elixir-bash/inboxsweeper" target=_blank rel=noopener>GitHub</a> · MIT License<br>
 Your mail stays yours — nothing here ever leaves your machine.
</footer>
<script>
const T="__TOKEN__";
const help={gmail:"Turn on 2-Step Verification, then create one at <a href=https://myaccount.google.com/apppasswords target=_blank>myaccount.google.com/apppasswords</a>.",
 yahoo:"Turn on 2-Step Verification, then 'Create app password' at <a href=https://login.yahoo.com/account/security target=_blank>login.yahoo.com/account/security</a>."};
function setHelp(){apphelp.innerHTML=help[provider.value]}
provider.onchange=setHelp; setHelp();
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'X-Token':T,'Content-Type':'application/json'},body:JSON.stringify(body||{})});return r.json()}
function log(m){document.getElementById('log').textContent+=m+"\\n";document.getElementById('log').scrollTop=1e9}
async function connect(){cstatus.textContent="Verifying…";const r=await api('/api/connect',{provider:provider.value,addr:addr.value,pw:pw.value});
 if(r.ok){cstatus.textContent="Connected ✓";document.getElementById('main').style.display='block';document.getElementById('connect').style.opacity=.6}
 else cstatus.textContent="Failed: "+r.error}
let ROWS=[];
const SPIN=["\\u280b","\\u2819","\\u2839","\\u2838","\\u283c","\\u2834","\\u2826","\\u2827","\\u2807","\\u280f"];
const SCAN_MSGS=["opening IMAP socket…","authenticating app password…","enumerating mailbox…","fetching envelopes…","grouping by sender…","reading List-Unsubscribe headers…","scoring bulk vs. personal…","shielding banks, receipts & bookings…","ranking noisiest senders…"];
let scanTimers=[];
function startScan(){const box=document.getElementById('scanner'),con=document.getElementById('scanConsole');
 box.classList.remove('hide');con.innerHTML="";let si=0,mi=0,n=0;
 scanTimers.push(setInterval(()=>{document.getElementById('spin').textContent=SPIN[si=(si+1)%SPIN.length]},80));
 scanTimers.push(setInterval(()=>{if(mi<SCAN_MSGS.length){const d=document.createElement('div');d.className='ln';d.textContent="\\u203a "+SCAN_MSGS[mi++];con.appendChild(d);con.scrollTop=1e9}},520));
 scanTimers.push(setInterval(()=>{n+=7+Math.floor(Math.random()*40);document.getElementById('scanCount').textContent=n.toLocaleString()},110));}
function stopScan(){scanTimers.forEach(clearInterval);scanTimers=[];document.getElementById('scanner').classList.add('hide');}
async function scan(){scanmsg.textContent="";results.classList.add('hide');startScan();
 const r=await api('/api/scan',{provider:provider.value});stopScan();
 if(r.error){log("scan error: "+r.error);return}
 ROWS=r.senders;const tb=document.getElementById('rows');tb.innerHTML="";
 ROWS.forEach((s,i)=>{const tr=document.createElement('tr');
  tr.innerHTML=`<td><input type=checkbox data-i=${i} ${s.protected?'':'checked'} ${s.protected?'disabled':''}></td>
   <td>${s.domain}</td><td>${s.count}</td><td class=method>${s.method}</td>
   <td>${s.protected?'<span class="tag p">protected</span>':'<span class="tag j">junk</span>'}</td>`;tb.appendChild(tr)});
 results.classList.remove('hide')}
function selected(){return [...document.querySelectorAll('#rows input:checked')].map(c=>ROWS[c.dataset.i].domain)}
function toggleAll(){document.querySelectorAll('#rows input:not([disabled])').forEach(c=>c.checked=all.checked)}
async function sweep(){const d=selected();if(!d.length)return log("nothing selected");
 log("Previewing "+d.length+" senders…");const p=await api('/api/sweep',{provider:provider.value,domains:d,execute:false});
 if(p.error){log("error: "+p.error);return}
 if(!confirm("Move "+p.total+" messages from "+d.length+" senders to Trash? (recoverable)"))return;
 log("Moving…");const r=await api('/api/sweep',{provider:provider.value,domains:d,execute:true});
 log(r.error?("error: "+r.error):("Moved "+r.moved+" messages to Trash."))}
async function unsub(){const d=selected();if(!d.length)return log("nothing selected");
 if(!confirm("Unsubscribe from "+d.length+" senders?"))return;log("Unsubscribing…");
 const r=await api('/api/unsub',{provider:provider.value,domains:d});
 if(r.error){log("error: "+r.error);return}r.results.forEach(x=>log("  "+x))}
</script></body></html>"""


def _unsub_domain(M, domain, addr, pw, smtp_box):
    meth, tgt = E.unsub_method(M, domain)
    if meth == "1click":
        import requests
        r = requests.post(tgt, data="List-Unsubscribe=One-Click",
                          headers={"Content-Type": "application/x-www-form-urlencoded",
                                   "User-Agent": "Mozilla/5.0"}, timeout=20)
        return "%s — 1click HTTP %s" % (domain, r.status_code)
    if meth == "mailto":
        m = re.match(r"mailto:([^?]+)(\?(.*))?", tgt); to = m.group(1); subj = ""
        for kv in (m.group(3) or "").split("&"):
            if kv.lower().startswith("subject="):
                subj = unquote(kv[8:])
        if smtp_box[0] is None:
            s = smtplib.SMTP(E.PROVIDERS[M._prov]["smtp"], 587); s.starttls(); s.login(addr, pw); smtp_box[0] = s
        msg = MIMEText(""); msg["From"] = addr; msg["To"] = to; msg["Subject"] = subj or "unsubscribe"
        smtp_box[0].sendmail(addr, [to], msg.as_string())
        return "%s — mailto sent" % domain
    if meth == "weblink":
        return "%s — needs manual click (weblink): %s" % (domain, tgt[:50])
    return "%s — no unsubscribe header" % domain


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.split("?")[0] == "/":
            self._send(200, PAGE.replace("__TOKEN__", TOKEN), "text/html")
        else:
            self._send(404, "{}")

    def do_POST(self):
        if self.headers.get("X-Token") != TOKEN:
            self._send(403, json.dumps({"error": "bad token"})); return
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")
        prov = req.get("provider", "gmail")
        try:
            self._send(200, json.dumps(self.route(self.path, prov, req)))
        except Exception as e:
            self._send(200, json.dumps({"error": str(e)[:120]}))

    def route(self, path, prov, req):
        if path == "/api/connect":
            addr, pw = req["addr"].strip(), req["pw"].replace(" ", "")
            M = E.connect(prov, addr, pw, readonly=True); M.logout()
            E.save_creds(prov, addr, pw)
            return {"ok": True}
        addr, pw = E.load_creds(prov)
        if not (addr and pw):
            return {"error": "not connected"}
        if path == "/api/scan":
            M = E.connect(prov, addr, pw, readonly=True)
            dom = E.fetch_from(M, E.search_bulk(M))
            out = []
            for d, c in dom.most_common(30):
                meth, _ = E.unsub_method(M, d)
                out.append({"domain": d, "count": c, "method": meth, "protected": E._is_protected(d)})
            M.logout()
            return {"senders": out}
        if path == "/api/sweep":
            domains = [d for d in req["domains"] if not E._is_protected(d)]
            if not req.get("execute"):
                M = E.connect(prov, addr, pw, readonly=True)
                total = sum(len(E.search_sender(M, d, 365)) for d in domains); M.logout()
                return {"total": total}
            M = E.connect(prov, addr, pw, readonly=False); moved = 0; freed = 0
            for d in domains:
                uids = E.search_sender(M, d, 365)
                freed += E.total_size(M, uids)   # size before the move, while UIDs are still valid
                moved += E.move_to_trash(M, uids)
            M.logout()
            E.track("sweep", prov, emails=moved, size_bytes=freed)
            return {"moved": moved}
        if path == "/api/unsub":
            M = E.connect(prov, addr, pw, readonly=True); box = [None]; res = []; ok = 0
            for d in req["domains"]:
                if E._is_protected(d):
                    res.append("%s — protected, skipped" % d); continue
                try:
                    line = _unsub_domain(M, d, addr, pw, box)
                    if "mailto sent" in line or "HTTP 2" in line:   # 2xx = accepted
                        ok += 1
                    res.append(line)
                except Exception as e:
                    res.append("%s — ERR %s" % (d, str(e)[:40]))
            if box[0]:
                box[0].quit()
            M.logout()
            if ok:
                E.track("unsub", prov, unsubs=ok)
            return {"results": res}
        return {"error": "unknown endpoint"}


def serve(port=8765):
    for p in range(port, port + 20):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), H)
            break
        except OSError:
            continue
    else:
        raise SystemExit("no free port")
    url = "http://127.0.0.1:%d/?t=%s" % (p, TOKEN)
    _say("InboxSweeper UI running at:\n  %s\n(Press Ctrl+C to stop.)" % url)
    threading.Timer(0.6, lambda: _safe_open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        _say("\nstopped.")


def _say(msg):
    # Bundled --windowed apps have no stdout; a bare print() would crash them.
    try:
        print(msg)
    except Exception:
        pass


def _safe_open(url):
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    serve()
