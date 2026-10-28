"""Saansathi: dependency-free Python web app with an optional Nebius model."""

from __future__ import annotations

import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"


def load_env() -> None:
    if os.getenv("SAANSATHI_DEMO_MODE", "").lower() == "true":
        return
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$", line)
            if match and not os.getenv(match.group(1)):
                os.environ[match.group(1)] = match.group(2).strip("\"'")
    except OSError:
        pass


load_env()
MODEL = os.getenv("NEBIUS_MODEL", "nvidia/Nemotron-3_5-Lightning")
EMERGENCY = re.compile(
    r"\b(can't breathe|cannot breathe|struggling to breathe|severe shortness of breath|"
    r"blue lips|blue face|unconscious|passed out|crushing chest pain|severe chest pain)\b",
    re.I,
)
URGENT_TEXT = (
    "Your message mentions symptoms that can be an emergency. Please contact your local "
    "emergency number or go to the nearest emergency department now. Do not wait for an AI "
    "response. If possible, ask someone nearby to stay with you."
)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def guide(message: str, details: str, language: str = "English") -> tuple[str, bool]:
    text = "\n".join(part for part in (details, message) if part)
    if EMERGENCY.search(text):
        return URGENT_TEXT, True
    key = os.getenv("NEBIUS_API_KEY", "")
    if not key or os.getenv("SAANSATHI_DEMO_MODE", "").lower() == "true":
        if message and not details:
            return (
                "For a clinician visit, note when the cough or breathing symptoms began, "
                "whether they are changing, and what makes them better or worse. I can’t "
                "assess the cause here. If symptoms persist, worsen, or concern you, contact "
                "a qualified clinician.\n\nNext step: write down your symptoms and duration "
                "to share with a clinician.",
                False,
            )
        return (
            f"Visit notes: {details}\n\nYou can add when symptoms began, whether they are "
            "changing, and any questions for a clinician. If symptoms persist, worsen, or "
            "concern you, contact a qualified clinician.",
            False,
        )
    base = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1").rstrip("/")
    system = (
        f"You are Saansathi, a calm respiratory-care navigation assistant for adults. Reply in {language}. "
        "Provide general health education and help prepare for a clinician conversation. Do not diagnose, "
        "interpret test results, recommend prescriptions, assign risk scores, or replace professional care. "
        "For severe trouble breathing, blue lips/face, fainting, or severe chest pain, tell the user to contact "
        "local emergency services now. Ask at most one short follow-up question. Use simple, concise language, "
        "do not request identifying details, and end with one practical next step."
    )
    body = json.dumps({
        "model": MODEL,
        "temperature": 0.25,
        "max_tokens": 420,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}],
    }).encode()
    req = Request(
        base + "/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=45) as response:
            result = json.loads(response.read())
        answer = result["choices"][0]["message"]["content"].strip()
        if not answer:
            raise ValueError("Empty response")
        return answer, False
    except HTTPError as exc:
        if exc.code in (401, 403):
            return "Nebius did not accept this API key. Check the token and model access.", False
        return f"Nebius request failed ({exc.code}). Check your model ID and try again.", False
    except (URLError, TimeoutError, ValueError, KeyError, IndexError, json.JSONDecodeError):
        return "Could not get a response from Nebius. Check the connection and try again.", False


def page(result: str = "", urgent: bool = False, selected: list[str] | None = None,
         note: str = "", duration: str = "", question: str = "", language: str = "English") -> bytes:
    selected = selected or []
    status = "Offline demo · no billing needed" if not os.getenv("NEBIUS_API_KEY") or os.getenv("SAANSATHI_DEMO_MODE", "").lower() == "true" else f"{esc(MODEL)} · connected"
    checks = ["Cough", "Shortness of breath", "Wheezing", "Chest discomfort", "Congestion", "Sore throat", "Fever", "Fatigue"]
    choices = "".join(
        f'<label class="chip"><input type="checkbox" name="symptom" value="{esc(item)}"{" checked" if item in selected else ""}><span>{esc(item)}</span></label>'
        for item in checks
    )
    opts = ["", "Today", "A few days", "About a week", "More than two weeks", "It comes and goes"]
    duration_options = "".join(f'<option value="{esc(item)}"{" selected" if item == duration else ""}>{esc(item or "How long has this been happening?")}</option>' for item in opts)
    reply = f'<section class="answer{" urgent" if urgent else ""}" role="status"><h3>{"Urgent help" if urgent else "Your guidance"}</h3><p>{esc(result).replace(chr(10), "<br>")}</p></section>' if result else ""
    content = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1115"><title>Saansathi — a clearer next step</title><link rel="stylesheet" href="/styles.css"></head><body>
<div class="shell"><aside class="rail"><a class="brand" href="#home"><span class="brand-mark">✳</span><span>saansathi<span class="brand-dot">.</span></span></a><div class="rail-label">YOUR SPACE</div><nav class="nav-list"><a class="nav-item active" href="#home">⌂　Overview</a><a class="nav-item" href="#check-in">＋　Symptom check-in</a><a class="nav-item" href="#ask">✳　Ask Saansathi</a></nav><div class="rail-spacer"></div><div class="privacy-card"><div><strong>Your space is yours</strong><p>Your notes are not saved. Please skip names and personal details.</p></div></div><div class="rail-footer"><span class="status-dot"></span><span>{status}</span></div></aside>
<main id="home" class="main"><header class="topbar"><div class="breadcrumb">Your space　/　<strong>Overview</strong></div><span class="today-label">Saansathi · Python</span></header><section class="welcome"><div class="welcome-copy"><span class="eyebrow">A LITTLE MORE CLARITY</span><h1>Your next step,<br><span>at your pace.</span></h1><p>Organize what you’re feeling and prepare for a care conversation, one small step at a time.</p><a class="primary-button" href="#check-in">Start a check-in　↗</a></div><div class="welcome-art"><div class="sun"></div><div class="hill hill-back"></div><div class="hill hill-front"></div><div class="art-caption">Breathe in.<br>Take it from here.</div></div></section>
<div class="content-grid"><section id="check-in" class="panel checkin-panel"><span class="section-kicker">01 · YOUR CHECK-IN</span><h2>What’s on your mind?</h2><p class="panel-intro">Share only what you’re comfortable with. This helps organize your thoughts, not diagnose a condition.</p><form method="post" action="/checkin"><fieldset><legend class="field-label">What have you noticed?</legend><div class="symptoms">{choices}</div></fieldset><label class="field-label" for="note">Anything else you’d like to note?</label><textarea id="note" name="note" maxlength="2000" placeholder="For example: It feels worse at night…">{esc(note)}</textarea><div class="field-row"><select name="duration" aria-label="How long?">{duration_options}</select><button class="primary-button" type="submit">Make my care notes ↗</button></div></form>{reply}</section>
<aside class="side-column"><section class="panel nextstep-panel"><span class="section-kicker">YOUR NEXT STEP</span><h3>Start with what<br>you already know.</h3><p>A rough note about when things started and what changed is a good beginning.</p></section><section class="panel safety-panel"><strong>Need urgent help?</strong><p>If you’re struggling to breathe, have severe chest pain, feel faint, or notice blue lips, seek emergency care now.</p></section></aside></div>
<section id="ask" class="panel ask-panel"><span class="section-kicker">02 · ASK SAANSATHI</span><h2>A question, a little less worry.</h2><p>Get general information or help figuring out what to ask a clinician. Saansathi cannot diagnose or replace a care professional.</p><form method="post" action="/ask"><textarea name="question" maxlength="2000" placeholder="Ask about your next step…">{esc(question)}</textarea><div class="field-row"><select name="language"><option{" selected" if language == "English" else ""}>English</option><option{" selected" if language == "Bahasa Indonesia" else ""}>Bahasa Indonesia</option></select><button class="primary-button" type="submit">Ask Saansathi ↑</button></div></form>{reply}</section><footer class="disclaimer">Saansathi is a care-navigation demo, not a medical service. For ongoing or worsening symptoms, contact a qualified clinician.</footer></main></div></body></html>'''
    return content.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            configured = bool(os.getenv("NEBIUS_API_KEY")) and os.getenv("SAANSATHI_DEMO_MODE", "").lower() != "true"
            body = json.dumps({"ok": True, "provider": "Nebius Token Factory" if configured else "Offline demo", "model": MODEL, "configured": configured, "demoMode": not configured}).encode()
            self.send(200, body, "application/json; charset=utf-8")
        elif self.path == "/styles.css":
            try:
                self.send(200, (PUBLIC / "styles.css").read_bytes(), "text/css; charset=utf-8")
            except OSError:
                self.send(404, b"Not found", "text/plain")
        elif self.path in ("/", "/index.html"):
            self.send(200, page())
        else:
            self.send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 16_000:
            self.send(413, page("Please keep your note under 16 KB."))
            return
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"), keep_blank_values=True)
        get = lambda name: form.get(name, [""])[0][:3000].strip()
        selected = [value[:80] for value in form.get("symptom", [])[:8]]
        if self.path == "/checkin":
            details = ", ".join(selected + ([get("note")] if get("note") else []))
            if get("duration"):
                details += f" (Duration: {get('duration')})"
            if not details:
                self.send(200, page("Choose a symptom or add a short note first."))
                return
            answer, urgent = guide("Help me make a brief, neutral summary I can share with a clinician. Include only the symptoms and duration I gave you; do not infer a diagnosis.", details)
            self.send(200, page(answer, urgent, selected, get("note"), get("duration")))
        elif self.path == "/ask":
            question = get("question")
            if not question:
                self.send(200, page("Add a question first."))
                return
            language = get("language") if get("language") == "Bahasa Indonesia" else "English"
            answer, urgent = guide(question, "", language)
            self.send(200, page(answer, urgent, question=question, language=language))
        else:
            self.send(404, b"Not found", "text/plain")

    def log_message(self, _format: str, *_args: object) -> None:
        print(f"Saansathi request: {self.command} {self.path}")


if __name__ == "__main__":
    try:
        import streamlit as st
        streamlit_runtime = st.runtime.exists()
    except (ImportError, RuntimeError):
        st = None
        streamlit_runtime = False

    if st is not None and streamlit_runtime:
        st.set_page_config(page_title="Saansathi — a clearer next step", page_icon="🌿", layout="wide")
        st.markdown("""
        <style>
        .stApp{background:radial-gradient(ellipse at 82% 5%,#142820 0,transparent 38%),#0b1115;color:#e6f1ec}
        [data-testid="stSidebar"]{background:#0e1619;border-right:1px solid #202d2a}
        [data-testid="stMarkdownContainer"] p{font-size:16px;color:#b4c4bc}
        h1,h2,h3{color:#e6f1ec!important} .stButton>button{background:#35c394;color:#071912;border:0;min-height:44px;font-weight:700}
        .stTextArea textarea,.stTextInput input{background:#0e1719;color:#e2eee8}
        </style>
        """, unsafe_allow_html=True)
        configured = bool(os.getenv("NEBIUS_API_KEY")) and os.getenv("SAANSATHI_DEMO_MODE", "").lower() != "true"
        with st.sidebar:
            st.title("✳ Saansathi")
            st.caption("YOUR SPACE")
            st.markdown("Overview  ·  Symptom check-in  ·  Ask Saansathi")
            st.divider()
            st.markdown("**Your space is yours**\n\nYour notes are not saved. Skip names and personal details.")
            st.divider()
            st.caption(f"🟢 {MODEL} · connected" if configured else "🟢 Offline demo · no billing needed")
        st.caption("A LITTLE MORE CLARITY")
        st.title("Your next step, at your pace.")
        st.write("Organize what you’re feeling and prepare for a care conversation, one small step at a time.")
        st.divider()
        checkin_col, help_col = st.columns([1.7, 1])
        with checkin_col:
            st.subheader("01 · Your check-in")
            st.write("Share only what you’re comfortable with. This helps organize your thoughts, not diagnose a condition.")
            with st.form("checkin"):
                st.markdown("**What have you noticed?**")
                symptoms = ["Cough", "Shortness of breath", "Wheezing", "Chest discomfort", "Congestion", "Sore throat", "Fever", "Fatigue"]
                selected = [item for item in symptoms if st.checkbox(item, key=f"symptom_{item}")]
                note = st.text_area("Anything else you’d like to note?", max_chars=2000, placeholder="For example: It feels worse at night…")
                duration = st.selectbox("How long has this been happening?", ["", "Today", "A few days", "About a week", "More than two weeks", "It comes and goes"])
                submitted = st.form_submit_button("Make my care notes")
            if submitted:
                details = ", ".join(selected + ([note.strip()] if note.strip() else []))
                if duration:
                    details += f" (Duration: {duration})"
                if not details:
                    st.info("Choose a symptom or add a short note first.")
                else:
                    answer, urgent = guide("Help me make a brief, neutral summary I can share with a clinician. Include only the symptoms and duration I gave you; do not infer a diagnosis.", details)
                    (st.error if urgent else st.success)(answer)
        with help_col:
            st.subheader("Your next step")
            st.markdown("Start with what you already know. A rough note about when things started and what changed is a good beginning.")
            st.warning("**Need urgent help?** If you’re struggling to breathe, have severe chest pain, feel faint, or notice blue lips, seek emergency care now.")
        st.divider()
        st.subheader("02 · Ask Saansathi")
        st.write("Get general information or help figuring out what to ask a clinician. Saansathi cannot diagnose or replace a care professional.")
        with st.form("ask"):
            question = st.text_area("Your question", max_chars=2000, placeholder="Ask about your next step…")
            left, right = st.columns([1, 1])
            with left:
                language = st.selectbox("Reply language", ["English", "Bahasa Indonesia"])
            with right:
                ask_submitted = st.form_submit_button("Ask Saansathi")
        if ask_submitted:
            if not question.strip():
                st.info("Add a question first.")
            else:
                answer, urgent = guide(question.strip(), "", language)
                (st.error if urgent else st.info)(answer)
        st.caption("Saansathi is a care-navigation demo, not a medical service. For ongoing or worsening symptoms, contact a qualified clinician.")
    else:
        port = int(os.getenv("PORT", "3000"))
        server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        print(f"Saansathi Python server listening at http://localhost:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nSaansathi server stopped.")
        finally:
            server.server_close()
