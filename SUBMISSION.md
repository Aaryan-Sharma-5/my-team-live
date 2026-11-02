# Submission note

Artifact: https://my-team-live.onrender.com/

Fans following a fantasy XI can miss which match moments affect their players and why their points change.

My Team Live replays the 2023 IPL final from the perspective of a chosen XI. Fans can follow personalized updates, see the exact calculation behind each points change, and check their players' contributions. The match is clearly labeled as a replay and uses a simplified scoring system.

With the default XI, captain Ravindra Jadeja hits a six and a four off the final two balls, adding 26 points as Chennai wins the final. Both come off Mohit Sharma, who is also in the XI, a mixed moment any fan would recognize.

Scoring is deterministic Python code. Default-team updates were pre-generated with Codex from match facts; custom teams can use GPT-OSS 20B via Groq, with a template fallback if AI is unavailable. I used Codex to help build and test the app.

