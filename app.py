"""Tiny local web page for the family member who sets it up.

Run:  python app.py   then open http://localhost:5000
One big button plays today's walk. After the walk, log how it went.
"""
from datetime import date

from flask import Flask, redirect, render_template_string, request, send_from_directory

import tracing
from config import AUDIO_DIR, load_profile
from memory import get_memory
from stroll import make_today

app = Flask(__name__)
tracing.init()

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stroll Call</title>
<style>
 :root{--bg:#f6f3ec;--ink:#1f2a1f;--accent:#2f6b3a;--muted:#6b6b6b;--card:#fff}
 @media (prefers-color-scheme:dark){:root{--bg:#141714;--ink:#e9efe7;--accent:#7cc58a;--muted:#9aa39a;--card:#1d221d}}
 body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.5 system-ui,sans-serif}
 main{max-width:640px;margin:0 auto;padding:24px 16px}
 h1{font-size:28px;margin:0 0 4px} .sub{color:var(--muted);margin:0 0 24px}
 .card{background:var(--card);border-radius:14px;padding:20px;margin-bottom:20px}
 button{font-size:22px;padding:18px 24px;border:0;border-radius:12px;background:var(--accent);color:#fff;width:100%;cursor:pointer}
 .nudge{font-size:21px} audio{width:100%;margin-top:14px}
 label{display:block;margin-top:12px} input,select{font-size:18px;padding:10px;width:100%;box-sizing:border-box;border-radius:8px;border:1px solid #bbb}
 .meta{color:var(--muted);font-size:14px;margin-top:10px}
 table{width:100%;border-collapse:collapse;font-size:15px} td{padding:6px 4px;border-top:1px solid #8883;vertical-align:top}
</style></head><body><main>
<h1>Stroll Call</h1>
<p class="sub">Today's walk for {{ name }}. Press play, then put the phone away.</p>
<div class="card">
 {% if row and row.nudge %}
  <div class="nudge">{{ row.nudge }}</div>
  {% if row.meta.audio %}<audio controls autoplay src="/audio/{{ row.meta.audio }}"></audio>{% endif %}
  <div class="meta">{{ row.meta.model }} · {{ row.meta.latency_ms }} ms · {{ row.meta.input_tokens }}/{{ row.meta.output_tokens }} tokens</div>
  <form method="post" action="/generate"><input type="hidden" name="force" value="1">
   <button style="margin-top:16px;background:#666">Make a different one</button></form>
 {% else %}
  <form method="post" action="/generate"><button>Make today's walk</button></form>
 {% endif %}
</div>
<div class="card"><h2 style="margin-top:0">After the walk</h2>
<form method="post" action="/log">
 <label>Minutes walked <input name="minutes" type="number" min="0" max="240" required></label>
 <label>How did it feel?
  <select name="felt"><option>great</option><option selected>good</option><option>okay</option><option>tired</option><option>did not go</option></select></label>
 <label>Anything to remember? <input name="note" placeholder="e.g. chatted with the nursery owner"></label>
 <button style="margin-top:16px">Save</button>
</form></div>
<div class="card"><h2 style="margin-top:0">Recent walks</h2><table>
{% for r in history %}<tr><td>{{ r.date }}</td><td>{% if r.walk %}{{ r.walk.minutes }} min, {{ r.walk.felt }}{% else %}-{% endif %}</td><td>{{ r.walk.note if r.walk else '' }}</td></tr>{% endfor %}
</table></div>
</main></body></html>"""


def _ctx():
    profile = load_profile()
    mem = get_memory(profile["name"])
    return profile, mem


@app.get("/")
def index():
    profile, mem = _ctx()
    return render_template_string(PAGE, name=profile["name"],
                                  row=mem.get(date.today().isoformat()), history=mem.recent(10))


@app.post("/generate")
def gen():
    make_today(force=bool(request.form.get("force")))
    return redirect("/")


@app.post("/log")
def log():
    _, mem = _ctx()
    mem.log_walk(date.today().isoformat(), int(request.form["minutes"]),
                 request.form.get("felt", "good"), request.form.get("note", ""))
    return redirect("/")


@app.get("/audio/<path:name>")
def audio(name):
    return send_from_directory(AUDIO_DIR, name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
