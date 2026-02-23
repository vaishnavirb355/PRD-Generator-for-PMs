# ─────────────────────────────────────────────────────────────────────────────
# PRD Generator — AI Product Co-Pilot
# Copyright (c) 2026 Vaishnavi R.B. All rights reserved.
#
# This software is the intellectual property of Vaishnavi R.B.
# Unauthorised copying, modification, or distribution of this file,
# via any medium, is strictly prohibited.
#
# Built as part of an AI Product Manager portfolio.
# Contact: github.com/vaishnavirb
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import ollama
import re
import io
import hashlib
from datetime import datetime

# ── Compatibility patch ───────────────────────────────────────────────────────
# Some macOS/OpenSSL versions don't support the `usedforsecurity` kwarg that
# ReportLab passes internally to hashlib.md5(). This patch ensures it works
# across all environments.
_original_md5 = hashlib.md5
def _patched_md5(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _original_md5(*args, **kwargs)
hashlib.md5 = _patched_md5
# ─────────────────────────────────────────────────────────────────────────────

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PRD Generator · AI Co-Pilot",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_MODEL = "llama3.1:8b"

SYSTEM_PROMPT = """You are an expert AI Product Manager assistant that writes world-class Product Requirements Documents (PRDs).

Your conversational process:
1. When the user describes a feature or product idea, ask EXACTLY ONE sharp discovery question at a time. Do not list multiple questions. Ask one, wait for the answer, then ask the next. You need to cover these 5 areas across 5 turns (one per turn):
   - Turn 1: The core user problem being solved
   - Turn 2: Who the primary target users are
   - Turn 3: What success looks like (business goals / metrics)
   - Turn 4: Key constraints (timeline, team, tech stack, budget)
   - Turn 5: Any known risks or things deliberately out of scope
   After all 5 answers are collected, proceed to generate the PRD.
2. Select the best framework based on context:
   - Lenny's Newsletter style → well-scoped features for existing products (most common)
   - Amazon PRFAQ style → big bets, new products, major launches
   - Lean PRD → early-stage MVPs with high uncertainty
3. Generate the complete PRD wrapped EXACTLY in <PRD_START> and <PRD_END> tags.
4. Outside the tags, briefly explain which framework you chose and why, then offer 3 specific refinement options.

Every PRD must include these sections (adapt wording per framework):
# [Product/Feature Name] PRD
## Problem Statement
## Target Users & Personas
## Goals & Success Metrics
## Non-Goals
## User Stories / Jobs to Be Done
## Functional Requirements
## Non-Functional Requirements
## UX & Design Considerations
## Dependencies & Risks
## Open Questions
## Timeline & Phases

Writing style: Sharp, strategic, PM-native. Like a Senior PM at Atlassian or Canva. Specific metrics, no fluff.
CRITICAL: The ENTIRE PRD must be inside <PRD_START>...</PRD_END> tags. Only commentary goes outside."""


# ─────────────────────────────────────────────────────────────
# Utility functions (all defined before use)
# ─────────────────────────────────────────────────────────────

def get_available_models():
    try:
        result = ollama.list()
        return [m.model for m in result.models]
    except Exception:
        return []


def extract_prd(text: str):
    """Returns (prd_content | None, commentary)."""
    match = re.search(r"<PRD_START>([\s\S]*?)<PRD_END>", text)
    if match:
        prd = match.group(1).strip()
        commentary = re.sub(r"<PRD_START>[\s\S]*?<PRD_END>", "", text).strip()
        return prd, commentary
    return None, text


def extract_title(prd_content: str) -> str:
    match = re.search(r"^#\s+(.+)$", prd_content, re.MULTILINE)
    return match.group(1).strip() if match else f"PRD – {datetime.now().strftime('%d %b %Y')}"


def md_inline(text: str) -> str:
    """Convert markdown inline syntax to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*",     r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`",       r"<code>\1</code>", text)
    return text


def prd_to_html(content: str) -> str:
    """Render PRD markdown as HTML for the in-app viewer."""
    out, lines = [], content.split("\n")
    in_ul = in_ol = False

    def close():
        nonlocal in_ul, in_ol
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False

    for line in lines:
        if line.startswith("# "):
            close(); out.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            close(); out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            close(); out.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith(("- ", "* ")):
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{md_inline(line[2:])}</li>")
        elif re.match(r"^\d+\. ", line):
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{md_inline(re.sub(r'^[0-9]+. ', '', line))}</li>")
        elif line.startswith("---"):
            close(); out.append("<hr>")
        elif not line.strip():
            close(); out.append("<div style='height:5px'></div>")
        else:
            close(); out.append(f"<p>{md_inline(line)}</p>")

    close()
    return "\n".join(out)


def generate_pdf(prd_content: str, title: str) -> bytes:
    """Render PRD markdown to a styled PDF via ReportLab."""
    buf = io.BytesIO()

    NAVY = HexColor("#1e40af")
    DARK = HexColor("#0f172a")
    GREY = HexColor("#374151")
    DIM  = HexColor("#94a3b8")
    RULE = HexColor("#e2e8f0")

    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=22*mm, rightMargin=22*mm,
                            topMargin=20*mm, bottomMargin=20*mm, title=title)

    sH1  = ParagraphStyle("H1",  fontName="Helvetica-Bold", fontSize=22, textColor=DARK, spaceAfter=4,  leading=28)
    sH2  = ParagraphStyle("H2",  fontName="Helvetica-Bold", fontSize=9,  textColor=NAVY, spaceAfter=4,  leading=12, spaceBefore=16)
    sH3  = ParagraphStyle("H3",  fontName="Helvetica-Bold", fontSize=11, textColor=DARK, spaceAfter=3,  leading=14, spaceBefore=8)
    sBody = ParagraphStyle("Bd", fontName="Helvetica",      fontSize=10, textColor=GREY, spaceAfter=3,  leading=16)
    sBull = ParagraphStyle("Bl", fontName="Helvetica",      fontSize=10, textColor=GREY, spaceAfter=2,  leading=15, leftIndent=14)
    sMeta = ParagraphStyle("Mt", fontName="Helvetica",      fontSize=8,  textColor=DIM,  spaceAfter=2,  leading=11)

    def il(t):
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", t)
        t = re.sub(r"`(.+?)`",       r'<font face="Courier">\1</font>', t)
        return t

    story = [
        Paragraph("PRODUCT REQUIREMENTS DOCUMENT", sMeta),
        Spacer(1, 3),
        Paragraph(title, sH1),
        Spacer(1, 2),
        Paragraph(f"PRD Generator · AI Co-Pilot &nbsp;|&nbsp; {datetime.now().strftime('%d %B %Y')}", sMeta),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=14),
    ]

    for line in prd_content.split("\n"):
        if line.startswith("# "):
            pass  # Title already in header
        elif line.startswith("## "):
            story += [HRFlowable(width="100%", thickness=0.5, color=RULE, spaceBefore=6, spaceAfter=3),
                      Paragraph(line[3:].upper(), sH2)]
        elif line.startswith("### "):
            story.append(Paragraph(il(line[4:]), sH3))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph(f"• &nbsp;{il(line[2:])}", sBull))
        elif re.match(r"^\d+\. ", line):
            n   = re.match(r"^(\d+)\.", line).group(1)
            txt = re.sub(r"^\d+\. ", "", line)
            story.append(Paragraph(f"<b>{n}.</b> &nbsp;{il(txt)}", sBull))
        elif line.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=RULE, spaceBefore=2, spaceAfter=2))
        elif not line.strip():
            story.append(Spacer(1, 4))
        else:
            story.append(Paragraph(il(line), sBody))

    story += [
        Spacer(1, 14),
        HRFlowable(width="100%", thickness=0.5, color=RULE),
        Spacer(1, 3),
        Paragraph("© 2026 Vaishnavi R.B. · PRD Generator — AI Product Co-Pilot · All rights reserved.", sMeta),
    ]

    doc.build(story)
    return buf.getvalue()


def stream_ollama(messages: list, model: str):
    """Yield response chunks from Ollama."""
    api_msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    for chunk in ollama.chat(model=model, messages=api_msgs, stream=True):
        yield chunk["message"]["content"]


# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Space+Mono&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; }

.app-header { display:flex; align-items:center; gap:14px; padding-bottom:1.2rem; border-bottom:1px solid #e2e8f0; margin-bottom:1.5rem; }
.app-logo { width:40px; height:40px; border-radius:10px; background:linear-gradient(135deg,#1e40af,#7c3aed); display:flex; align-items:center; justify-content:center; font-size:1.1rem; color:white; }
.app-title { font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:700; color:#0f172a; margin:0; }
.app-sub   { font-family:'Space Mono',monospace; font-size:.62rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; }

.msg-user { background:linear-gradient(135deg,#1e40af,#2563eb); color:#fff; padding:.85rem 1.15rem; border-radius:18px 18px 4px 18px; margin:.4rem 0 .4rem 18%; line-height:1.65; font-size:.91rem; box-shadow:0 2px 12px rgba(30,64,175,.25); }
.msg-bot  { background:#fff; color:#1e293b; padding:.85rem 1.15rem; border-radius:18px 18px 18px 4px; margin:.4rem 18% .4rem 0; border:1px solid #e2e8f0; line-height:1.65; font-size:.91rem; box-shadow:0 2px 10px rgba(0,0,0,.05); }
.msg-lbl  { font-family:'Space Mono',monospace; font-size:.62rem; text-transform:uppercase; letter-spacing:.06em; color:#94a3b8; margin-bottom:3px; }
.msg-lbl-r { text-align:right; }

.prd-viewer { background:#fff; border-radius:12px; padding:2rem 2.5rem; border:1px solid #e2e8f0; line-height:1.75; box-shadow:0 4px 20px rgba(0,0,0,.06); }
.prd-viewer h1 { font-family:'Playfair Display',serif; color:#0f172a; border-bottom:2px solid #e2e8f0; padding-bottom:.4rem; }
.prd-viewer h2 { font-family:'Space Mono',monospace; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:#1e40af; margin-top:1.8rem; }
.prd-viewer h3 { color:#374151; font-weight:700; }
.prd-viewer ul, .prd-viewer ol { padding-left:1.4rem; }
.prd-viewer li { margin-bottom:.3rem; color:#374151; }
.prd-viewer p  { color:#374151; }
.prd-viewer strong { color:#0f172a; }
.prd-viewer code { background:#f1f5f9; padding:.1em .35em; border-radius:4px; font-family:'Space Mono',monospace; font-size:.83em; }
.prd-viewer hr { border:none; border-top:1px solid #e2e8f0; }

.dot-ok { display:inline-block; width:8px; height:8px; border-radius:50%; background:#22c55e; margin-right:5px; }
.sb-lbl { font-family:'Space Mono',monospace; font-size:.62rem; text-transform:uppercase; letter-spacing:.07em; color:#64748b; margin-bottom:.4rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────
for key, val in [("messages", []), ("prds", []), ("view_prd_idx", None), ("model", DEFAULT_MODEL)]:
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:.8rem;">⚙ Settings</div>', unsafe_allow_html=True)

    available = get_available_models()
    if available:
        st.markdown('<div class="sb-lbl">Ollama Model</div>', unsafe_allow_html=True)
        default_i = available.index(DEFAULT_MODEL) if DEFAULT_MODEL in available else 0
        st.session_state.model = st.selectbox("Model", available, index=default_i, label_visibility="collapsed")
        st.markdown('<div style="font-size:.75rem;color:#22c55e;margin-top:4px;"><span class="dot-ok"></span>Ollama connected</div>', unsafe_allow_html=True)
    else:
        st.error("Ollama not running.\n\n`ollama serve`")

    st.divider()
    st.markdown('<div class="sb-lbl">Generated PRDs</div>', unsafe_allow_html=True)

    if st.session_state.prds:
        for ri, item in enumerate(reversed(st.session_state.prds)):
            real_i = len(st.session_state.prds) - 1 - ri
            c1, c2 = st.columns([3, 1])
            with c1:
                short = item["title"][:26] + ("…" if len(item["title"]) > 26 else "")
                st.markdown(f'<div style="font-size:.8rem;font-weight:500;color:#1e293b">{short}</div>'
                            f'<div style="font-size:.65rem;color:#94a3b8;font-family:Space Mono,monospace">{item["timestamp"]}</div>',
                            unsafe_allow_html=True)
            with c2:
                if st.button("Open", key=f"sb_v{real_i}"):
                    st.session_state.view_prd_idx = real_i
                    st.rerun()
    else:
        st.markdown('<div style="font-size:.8rem;color:#94a3b8;font-style:italic">None yet</div>', unsafe_allow_html=True)

    st.divider()
    if st.button("↺ New Conversation", use_container_width=True):
        st.session_state.messages     = []
        st.session_state.view_prd_idx = None
        st.rerun()

    with st.expander("💡 Tips"):
        st.markdown("""
- Lead with the **user problem**, not the solution
- Name the **target product** (e.g. "REA Group app")
- Share **constraints** — timeline, team, tech stack
- After PRD, ask to **sharpen metrics** or **add edge cases**
        """)


# ─────────────────────────────────────────────────────────────
# App header
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="app-logo">✦</div>
  <div>
    <div class="app-title">PRD Generator</div>
    <div class="app-sub">AI Product Co-Pilot · Powered by Ollama</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PRD Viewer
# ─────────────────────────────────────────────────────────────
if st.session_state.view_prd_idx is not None:
    item = st.session_state.prds[st.session_state.view_prd_idx]

    col_back, col_dl = st.columns(2)
    with col_back:
        if st.button("← Back to Chat"):
            st.session_state.view_prd_idx = None
            st.rerun()
    with col_dl:
        pdf = generate_pdf(item["content"], item["title"])
        safe_name = re.sub(r"[^a-zA-Z0-9_\- ]", "", item["title"])[:40].replace(" ", "_")
        st.download_button("↓ Download PDF", data=pdf,
                           file_name=f"PRD_{safe_name}.pdf",
                           mime="application/pdf",
                           use_container_width=True, type="primary")

    st.markdown(f'<div class="prd-viewer">{prd_to_html(item["content"])}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Chat view
# ─────────────────────────────────────────────────────────────
else:
    # Welcome bubble
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("**Welcome to PRD Generator** — your AI product co-pilot. ✦\n\nI'll craft a professional PRD with you through a short conversation.\n\nTell me: **what feature or product are you building?** One sentence is fine — I'll ask the right discovery questions.")

    # Render full chat history
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            prd_c, commentary = extract_prd(msg["content"])
            with st.chat_message("assistant"):
                st.markdown(commentary)
                if prd_c:
                    title   = extract_title(prd_c)
                    prd_idx = next((j for j, p in enumerate(st.session_state.prds) if p["title"] == title), None)
                    if prd_idx is not None:
                        ca, cb = st.columns([2, 1])
                        with ca:
                            st.info(f"✦ **{title}** — PRD generated")
                        with cb:
                            if st.button("View & Download →", key=f"open_{i}"):
                                st.session_state.view_prd_idx = prd_idx
                                st.rerun()

    # Input — always rendered after history
    user_input = st.chat_input("Describe your feature, answer questions, or ask to refine a section…")

    if user_input:
        # 1. Show user bubble immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Save to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        # 3. Stream assistant response — visible immediately in the same pass
        buf = {"full": ""}
        with st.chat_message("assistant"):
            try:
                def _gen():
                    for chunk in stream_ollama(api_msgs, st.session_state.model):
                        buf["full"] += chunk
                        yield chunk

                st.write_stream(_gen())

            except Exception as e:
                buf["full"] = (f"⚠️ **Ollama connection error.**\n\n"
                               f"Run: `ollama serve`  \n"
                               f"Pull model: `ollama pull {st.session_state.model}`\n\n"
                               f"Error: `{e}`")
                st.error(buf["full"])

        # 4. Persist and rerun to render PRD button if needed
        full = buf["full"]
        st.session_state.messages.append({"role": "assistant", "content": full})

        prd_c, _ = extract_prd(full)
        if prd_c:
            st.session_state.prds.append({
                "title":     extract_title(prd_c),
                "content":   prd_c,
                "timestamp": datetime.now().strftime("%d %b, %H:%M"),
            })

        st.rerun()

# ─────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    text-align: center;
    padding: 1.2rem 0 0.5rem 0;
    margin-top: 2rem;
    border-top: 1px solid #e2e8f0;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #94a3b8;
    letter-spacing: 0.05em;
">
    © 2026 <strong style="color:#64748b">Vaishnavi R.B.</strong> &nbsp;·&nbsp; PRD Generator — AI Product Co-Pilot &nbsp;·&nbsp; All rights reserved.
</div>
""", unsafe_allow_html=True)