# ✦ PRD Generator — AI Product Co-Pilot

> A conversational AI tool that generates professional Product Requirements Documents through a guided chat — powered by Ollama (local LLMs), running 100% offline.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Copyright](https://img.shields.io/badge/©%202026-Vaishnavi%20R%20B.-blueviolet) ![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red) ![Ollama](https://img.shields.io/badge/Ollama-local-green) ![License](https://img.shields.io/badge/License-MIT-grey)

---

## 🎯 Problem This Solves

Writing PRDs from scratch is slow, inconsistent, and often skipped by junior PMs or engineers. Most templates are rigid and don't adapt to whether you're building a small feature vs. a new product.

This tool solves that by:
- Asking the **right discovery questions** before writing a single line of spec
- **Automatically selecting** the best PRD framework for the context
- Generating a **complete, professional PRD** in minutes
- Running **entirely locally** — no data leaves your machine

---

## 🧠 PRD Frameworks Supported

| Framework | When it's chosen |
|---|---|
| **Lenny's Newsletter style** | Well-scoped features for existing products |
| **Amazon PRFAQ** | Big bets, new products, major launches |
| **Lean PRD** | Early-stage MVPs with high uncertainty |

The AI selects the framework automatically based on your description and context.

---

## ⚙️ Tech Stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| LLM | Ollama (local) — `llama3.1:8b` recommended |
| PDF generation | ReportLab |
| Language | Python 3.10+ |
| Hosting | Runs 100% locally — no cloud, no API keys needed |

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### 2. Pull the recommended model

```bash
ollama pull llama3.1:8b
```

> **Low RAM (< 16GB)?** Use `llama3.2:3b` instead — nearly as good for document generation.

### 3. Clone & install

```bash
git clone https://github.com/vaishnavirb355/prd-generator.git
cd prd-generator
pip install -r requirements.txt
```

### 4. Run

```bash
# Make sure Ollama is running first
ollama serve

# In a new terminal
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 🖥️ How It Works

```
User describes feature idea
        ↓
AI asks 4-5 discovery questions
        ↓
User answers
        ↓
AI selects best PRD framework
        ↓
Full PRD generated (streamed live)
        ↓
View in-app or Download as PDF
```

### Key Features
- 💬 **Conversational interface** — guided discovery before writing
- 🔄 **Live streaming** — see the PRD generate in real time
- 📄 **PDF export** — styled, professional output with ReportLab
- 📚 **PRD history** — all generated PRDs saved in the sidebar this session
- 🔒 **100% local** — Ollama runs on your machine, zero data sent externally
- 🎛️ **Model switcher** — pick any Ollama model from the sidebar

---

## 📐 PRD Sections Generated

Every PRD includes:

1. **Problem Statement** — what pain exists and for whom
2. **Target Users & Personas** — primary and secondary users
3. **Goals & Success Metrics** — specific KPIs (HEART framework or North Star)
4. **Non-Goals** — explicit scope boundaries
5. **User Stories / Jobs to Be Done**
6. **Functional Requirements**
7. **Non-Functional Requirements** — performance, security, accessibility
8. **UX & Design Considerations** — key flows, edge cases
9. **Dependencies & Risks**
10. **Open Questions**
11. **Timeline & Phases** — Discovery / Alpha / Beta / GA

---

## 🗂️ Project Structure

```
prd-generator/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 💼 Portfolio Context

This project was built as part of a structured **AI Product Manager portfolio** to demonstrate:

- Deep understanding of PM artifacts (PRDs, discovery frameworks, success metrics)
- Practical AI engineering skills (LLM prompt engineering, Streamlit, local AI)
- Privacy-first product thinking — choosing local LLMs to avoid data exposure
- Real-world problem solving for a pain point every PM team faces

---

## 🔮 Potential Extensions

- [ ] Export to Notion / Confluence
- [ ] Add Claude API as an alternative LLM backend
- [ ] User interview summary → PRD pipeline
- [ ] PRD diff/versioning across refinement rounds
- [ ] Jira ticket auto-generation from functional requirements

---

## 📝 License

MIT License

Copyright (c) 2026 Vaishnavi R B.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software to use, copy, modify, and distribute it, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

---

*Built by [Vaishnavi R B](https://github.com/vaishnavirb355) · AI Engineer turning Product Strategist*
