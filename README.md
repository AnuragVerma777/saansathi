# Saansathi

**A clearer next step, at your pace.** Saansathi is a hackathon-ready respiratory care navigation demo. People can write down what they are experiencing, turn it into clinician-visit notes, and ask general respiratory health questions. Responses are generated with NVIDIA Nemotron through Nebius Token Factory.

The interface uses a dark, low-light visual system with a responsive mobile layout, guided symptom chips, and English or Bahasa Indonesia AI replies.

**Live demo:** A shared public instance still needs to be deployed. You can create a hosted copy from this repository with the button below; Render will ask you for a Nebius Token Factory API key before enabling AI responses.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AnuragVerma777/saansathi)

**Try the demo on Render:** [Open Saansathi](https://render.com/deploy?repo=https://github.com/AnuragVerma777/saansathi)

Saansathi is inspired by the broad community-health motivation behind Jaga, while taking a different product approach: it does not record or classify cough audio, calculate risk, triage people into categories, screen for TB, or offer a diagnosis. It helps people prepare for a care conversation. The application is a prototype, not a medical service.

## Run locally

Requirements: Node.js 20 or newer. No package install is needed; the server uses Node's built-in modules.

1. Copy `.env.example` to `.env`.
2. Add your Nebius Token Factory key as `NEBIUS_API_KEY`.
3. Set `NEBIUS_MODEL` to a Nemotron model available in your account, if needed.
4. Run `npm start` and open [http://localhost:3000](http://localhost:3000).

For PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
npm start
```

The API key is only read by the Node server and is never sent to the browser. Do not commit `.env`.

## Nebius configuration

The server calls the OpenAI-compatible `POST /chat/completions` endpoint at `https://api.tokenfactory.nebius.com/v1` using bearer authentication. The default model is `nvidia/Nemotron-3_5-Lightning`. Override these values in `.env` when a different base URL or model ID is required:

```dotenv
NEBIUS_API_KEY=...
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning
PORT=3000
```

The API key is required for AI responses. The interface explains when the key is missing; emergency warning signs are handled locally with a deterministic response.

## Demo flow

1. Select any symptoms that apply, add an optional note and duration.
2. Generate a short, neutral visit-preparation summary and copy it.
3. Ask a general question or tap one of the suggested prompts.
4. Open the urgent-help panel to see the emergency warning signs.

## Safety and privacy

- General information only. The model is instructed not to diagnose, give risk probabilities, prescribe medication, or replace clinical judgment.
- Severe breathing trouble, blue lips or face, fainting, and severe chest pain trigger a local emergency message before calling the model.
- For ongoing, worsening, or concerning symptoms, contact a qualified clinician. Do not wait for the chatbot in an emergency.
- The demo has no account or database. Notes remain in the page's memory and are sent to the configured Nebius API only when requesting AI assistance. Do not enter names or identifying details.
- This prompt and keyword check are demo safeguards, not validated medical-device controls.

## Deployment

### Render

The root [`render.yaml`](./render.yaml) is a Render Blueprint for the Node web service. To publish:

1. Click the **Deploy to Render** button above and sign in to Render.
2. Review the Saansathi web service and enter your Nebius Token Factory API key for `NEBIUS_API_KEY`; keep it in Render's environment settings, never in GitHub.
3. Deploy. Render will provide a public `onrender.com` address you can share with demo users.

The free service may spin down while idle, so its first request after a quiet period can take longer. No shared public URL has been created yet. See [Render's Deploy to Render guide](https://render.com/docs/deploy-to-render) for details about the one-click button and [Blueprint reference](https://render.com/docs/blueprint-spec) for the service configuration.

Use HTTPS and review the hosting provider's request logging and data retention before sharing the app publicly.
