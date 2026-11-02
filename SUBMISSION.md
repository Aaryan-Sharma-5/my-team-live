# Submission note draft

Artifact: https://my-team-live.onrender.com/

Fans following a fantasy XI can miss which match moments affect their players and why their points change.

My Team Live replays the 2023 IPL final from the perspective of a chosen XI. Fans can follow personalized updates, see the exact calculation behind each points change, and check their players' contributions. The match is clearly labeled as a replay and uses a simplified scoring system.

In the demo, captain Ravindra Jadeja hits a six and a four off the final two balls: the team gains 26 points while Chennai wins the final. Mohit Sharma, the bowler, is also in the XI—a small moment of mixed feelings for the fan.

The scoring is deterministic Python code. An optional GPT-OSS 20B integration via Groq turns selected structured match events into short Hinglish updates; a template fallback keeps the replay working without an API key or if the service fails. I used Codex to help build and test the app.

