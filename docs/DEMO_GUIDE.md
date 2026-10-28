# Demo walkthrough

## 90-second presentation

1. **Introduce the purpose:** Saansathi helps people prepare for a respiratory-care conversation. It does not diagnose or screen for a disease.
2. **Show the guided check-in:** Choose `Cough` and `Congestion`, select `A few days`, then add a short note such as “mostly at night.” Use only fictional, non-identifying demo details.
3. **Generate visit notes:** Show the concise summary and copy action. Explain that the model is asked to summarize only what the person supplied.
4. **Show Nemotron Q&A:** Tap a suggested question. Switch replies to Bahasa Indonesia to show multilingual response support.
5. **Show urgent-help handling:** Open **See urgent signs**. Explain that listed warning signs prompt emergency guidance before the model is called.
6. **Close with the stack:** Browser UI → Node.js server → Nebius Token Factory → NVIDIA Nemotron. The API key stays server-side.

## Setup before presenting

- Configure `NEBIUS_API_KEY` in local `.env` or in Render's secret environment variables.
- Confirm `/api/health` reports `configured: true`.
- Keep example input fictional; do not use real patient details.
- If presenting the Render-hosted copy, wake the free service before the demo because it can sleep while idle.

## Suggested narration

> “Saansathi turns a few user-selected symptoms into better questions for a clinician. Nemotron helps explain and organize information, while the app keeps urgent warning guidance and its medical boundaries visible.”
