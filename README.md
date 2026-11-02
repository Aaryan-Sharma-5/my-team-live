# My Team Live

A work-in-progress fantasy cricket replay. The match is a replay and uses simplified scoring; it is not live Dream11 data.

## Match source

Cricsheet match **1370353**, Gujarat Titans vs Chennai Super Kings, IPL final, 29 May 2023, Narendra Modi Stadium, Ahmedabad. The chase was rain-adjusted to 171 in 15 overs. The original JSON is in `backend/data/match.json`, from [Cricsheet's IPL JSON download](https://cricsheet.org/downloads/). Please retain attribution to Cricsheet when sharing this data.

Current ingestion check: 216 deliveries, 9 dismissals, 31 fours and 19 sixes. Final scores: Gujarat 214/4; Chennai 171/5. The default team is a demo selection, not a recommendation or an official fantasy lineup.

## Current status

Milestone 1: source data, normalized deliveries, default team and scoring values. Later milestones will add replay scoring, interface and optional AI narration.

Run the ingestion checks with `python -m pytest backend/tests/test_ingest.py -q`.
