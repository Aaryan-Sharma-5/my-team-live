type Team = {xi:string[]; captain:string; vice_captain:string};
type EventItem = {
  event:{batter:string;bowler:string;runs_batter:number;wicket:{player_out:string;kind:string}|null};
  match_state:{score:string;over:string;target:number|null};
  deltas:{player:string;final_points:number}[];
  team_total_after:number; tag:string;
};

export function narrationFacts(item:EventItem, team:Team) {
  const changes = new Map<string,number>();
  for (const delta of item.deltas) changes.set(delta.player, (changes.get(delta.player) ?? 0) + delta.final_points);
  // Include selected participants with no delta, for example the bowler hit for six.
  for (const name of [item.event.batter, item.event.bowler, item.event.wicket?.player_out]) {
    if (name && team.xi.includes(name) && !changes.has(name)) changes.set(name, 0);
  }
  const breakdown = [...changes].map(([player,points]) => ({player, points, role:player===team.captain?'captain':player===team.vice_captain?'vice-captain':'regular'}));
  const delta = item.deltas.reduce((sum,d) => sum + d.final_points, 0);
  return {
    event: item.event.wicket ? `${item.event.wicket.player_out} dismissed ${item.event.wicket.kind}; bowler ${item.event.bowler}` : `${item.event.batter} scored ${item.event.runs_batter} runs off ${item.event.bowler}`,
    team_points_delta: `${delta>=0?'+':''}${Number(delta.toFixed(1))}`,
    breakdown, team_total:item.team_total_after, score:item.match_state.score,
    over:item.match_state.over, target:item.match_state.target, tag:item.tag,
  };
}
