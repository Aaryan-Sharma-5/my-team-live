# Two-minute demo walkthrough

Open https://my-team-live.onrender.com/ about two minutes before the call: the free service may need time to wake. Start with the default XI and captain Jadeja. The replay defaults to 30×, around 72 seconds for 216 deliveries; actual timing depends on the browser. Keep it running while you explain.

1. **The fan problem (0:00–0:20).** “During a match, the broadcast follows the game. A fantasy fan is also watching eleven individual players and trying to understand which moments move their points. My Team Live brings those moments together from the perspective of their XI.” Point to the match-replay and simplified-scoring labels.

2. **Show the experience (0:20–0:55).** Tap **Start replay**. Show the score, points journey and key-moments feed. Use **Next key moment** if needed. On Gill's dismissal, point out the mixed-moment card: Gill is out, but captain Jadeja takes the wicket and the team gains 50 points. Expand a player in the lineup to show how their total was earned.

3. **Explain the trust boundary (0:55–1:20).** “Python calculates the points and captain multipliers. The language model phrases updates; it doesn't calculate the score.” Default-XI updates are labeled **AI (pre-generated)** and were created with Codex from the match facts. Custom teams can use GPT-OSS 20B via Groq; if it fails or a response fails validation, the app shows a template.

4. **Finish the story (1:20–1:40).** If the replay has reached the end, show Jadeja's six and four in **Five moments that mattered**. As captain, those balls add 16 and 10 points, taking the default team from 697 to 723. Both came off Mohit, who is also in the XI. The match result is Chennai's five-wicket DLS win.

5. **Trade-offs and next steps (1:40–2:00).** “I chose one recorded match so the demo is repeatable. The simplified rules omit stumpings, maidens and economy points; these are not official Dream11 scores. With authorized data, I'd connect the live feed and official points engine, then explore rank changes and timely alerts.”

If the replay is behind during the walkthrough, use **Next key moment**, or explain the ending using the highlights after it finishes. Avoid claiming that custom-team AI appears on every eligible ball: provider limits, timeouts and validation can cause template fallbacks.
