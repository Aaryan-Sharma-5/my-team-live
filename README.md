# My Team Live

A work-in-progress fantasy cricket replay. The match is a replay and uses simplified scoring; it is not live Dream11 data.

## Match source

Cricsheet match **1370353**, Gujarat Titans vs Chennai Super Kings, IPL final, 29 May 2023, Narendra Modi Stadium, Ahmedabad. The chase was rain-adjusted to 171 in 15 overs. The original JSON is in `backend/data/match.json`, from [Cricsheet's IPL JSON download](https://cricsheet.org/downloads/). Please retain attribution to Cricsheet when sharing this data.

Current ingestion check: 216 deliveries, 9 dismissals, 31 fours and 19 sixes. Final scores: Gujarat 214/4; Chennai 171/5. The default team is a demo selection, not a recommendation or an official fantasy lineup.

## Local development

Requires Python 3.11+ and Node.js. From the project root:

```sh
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000. The app serves the built frontend and API together. To work on the frontend separately, run `npm run dev` in `frontend` while the API runs on port 8000.

Run the backend checks with `python -m pytest backend/tests -q` (pytest is required for tests).

## Architecture and scoring

Cricsheet JSON → `ingest.py` normalizes deliveries → `scoring.py` calculates deterministic point deltas → `replay.py` builds the timeline → React plays the timeline locally. `GET /api/rules` exposes the same rules dictionary used by scoring. The source file lists the simplified rules and multipliers; they are also visible inside the app. They are not official Dream11 rules.

Selected events can be narrated by OpenAI GPT-OSS 20B via Groq and `/api/narrate`; the API key stays on the server. Output is checked for the supplied points figure and word limit. A missing key, timeout, API error, rate limit or failed check returns a deterministic template. The optional integration is configured by setting `GROQ_API_KEY` in the server environment; do not put keys in the frontend or commit them. `ALLOWED_ORIGINS` may be set to comma-separated origins if serving the frontend separately. The default same-origin setup does not need it.

The API integration and fallback are covered with mocked responses, but a real Groq request has not yet been verified with a key. The model's wording is constrained by a prompt and a basic number check; this is not a guarantee that every generated claim is correct.

## Container

With Docker running:

```sh
docker build -t my-team-live .
docker run --rm -p 8000:8000 my-team-live
```

For optional narration, pass the key as an environment variable using your hosting provider's secret settings. The container serves one public port, honoring `PORT` when supplied.

The public replay is at https://my-team-live.onrender.com/. Render's free instance can take time to wake after inactivity.

See [SUBMISSION.md](SUBMISSION.md) and [DEMO.md](DEMO.md) for the draft note and demo outline.
