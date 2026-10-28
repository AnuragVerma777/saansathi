# Demo walkthrough

## Video intro

**English:** “Hi, this is Saansathi, a respiratory-care navigation demo. It helps someone organize symptoms and prepare useful notes and questions for a clinician. It does not diagnose or replace medical care. When Nebius is configured, NVIDIA Nemotron powers the general question-and-answer and note-preparation flows.”

**Hinglish:** “Hi, yeh Saansathi hai—respiratory care ke liye ek guidance demo. Isse user apne symptoms ko organize karke doctor se baat karne ke liye notes aur questions prepare kar sakta hai. Yeh diagnosis nahi karta aur medical care ka replacement nahi hai. Nebius configured ho, toh Q&A aur notes mein NVIDIA Nemotron help karta hai.”

## 90-second video walkthrough

1. **Start on the introduction screen:** Explain the problem, audience, three-step flow, and the visible connection status. Select **Explore the demo** to continue.
2. **Show the guided check-in:** Choose `Cough` and `Congestion`, select `A few days`, then add a short note such as “mostly at night.” Use only fictional, non-identifying demo details.
3. **Generate visit notes:** Show the concise summary with the supplied symptoms and duration. Explain that the guide helps prepare information to share with a clinician.
4. **Show Q&A:** Tap a suggested question and point out the next-step guidance. If a model API is configured, describe this as Nemotron-powered; if the header says **Offline demo**, explain that it is a prepared example response and skip model claims.
5. **Show urgent-help handling:** Open **See urgent signs**. Explain that listed warning signs prompt emergency guidance before the model is called.
6. **Close with the stack:** When connected: browser → Python server → Nebius Token Factory → NVIDIA Nemotron. The API key stays server-side. In offline demo mode, the prepared guide works without Nebius billing or a key.

## Setup before presenting

- For an offline recording, start with `$env:SAANSATHI_DEMO_MODE='true'; python app.py`; no API key or billing is needed. Confirm the app header says **Offline demo**.
- For actual Nemotron responses, configure `NEBIUS_API_KEY` in local `.env` or Streamlit Cloud secrets.
- Keep example input fictional; do not use real patient details.
- Open the hosted [Streamlit demo](https://saansathi-ypc83mz5xbocxdu9xmoedv.streamlit.app/) before recording and allow time for it to load.

## Suggested narration

> “Saansathi turns a few user-selected symptoms into better questions for a clinician. Nemotron helps explain and organize information, while the app keeps urgent warning guidance and its medical boundaries visible.”

Only use the Nemotron sentence when the model is connected. In offline demo mode, say: “This recording uses prepared example responses so the demo can run without an API key.”
