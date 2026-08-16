# InsightAI — Demo Video Script

Record at 1080p / 60fps. Total runtime ~3 minutes. OBS or any screen
recorder works; capture only the app window at fullscreen wide layout.

---

## 0. Setup (0:00–0:15)
- `streamlit run app.py` from the repo root.
- Ensure the Chat page (default) is showing the hero with the InsightAI logo.

## 1. Upload a document (0:15–0:50) — **Document RAG**
- Place a new PDF in `data/raw/` before launching, then restart the app so it
  re-indexes ("Setting up InsightAI (indexing documents)…" spinner appears).
- In Chat, ask:
  > "What is driving customer churn and what caused it?"
- Narrate: the router sent it to internal reports; note the **sources /
  confidence** chips under the reply.
- Open the "confidence" chip and point to the deterministic reasons list.

## 2. SQL analytics (0:50–1:25)
- Ask:
  > "What was total revenue by category, and which category is strongest?"
- Narrate the live SQL path (read-only, row-limited). Open the **LLM calls**
  chip to show the budget/token readout. Mention the validator blocks anything
  but single SELECTs.
- Open the **Dashboard** page and show Revenue by category / confidence trend.

## 3. Web intelligence (1:25–1:50)
- Ask:
  > "How might current interest rates affect Northwind Traders' sales?"
- Show the "N sources" chip with real links.

## 4. Agent v2 (1:50–2:20)
- Switch AI mode to **Agent (v2)** and ask:
  > "Compare our sales performance with current inflation, based on our internal reports."
- Expand the **"N step(s)"** chip to show the tool-call trace (SQL → RAG → Web).

## 5. Executive report + performance (2:20–2:50)
- Open **Executive report** → Generate report → show summary + confidence badges.
- Open **Performance** monitor → show live call budget, tokens, index/chunks.

## 6. Wrap (2:50–3:00)
- Point to the conflict-handling behavior: ask a question whose sources disagree
  and show the warning chip + "Conflicting data detected".

---

## Tips
- Do a dry run first; the first LLM call per question is slower (cold cache).
- Disable OS notifications and hide your taskbar for a clean capture.
- Keep the terminal out of frame; all logging is on stdout and won't interfere.

## Suggested caption
"InsightAI — a business-analytics copilot that routes questions across your
sales database, internal reports, and the web, then shows you its confidence."
