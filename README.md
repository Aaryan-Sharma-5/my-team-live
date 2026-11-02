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

## Current status

The deterministic replay and template-only interface are in progress. AI narration and deployment have not been completed.
