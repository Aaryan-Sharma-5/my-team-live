import { expect, test } from 'vitest';
import { narrationFacts } from './narrationFacts';

test('wicket facts distinguish team change from each player', () => {
  const facts = narrationFacts({
    event: {batter:'Rashid Khan',bowler:'M Pathirana',runs_batter:0,wicket:{player_out:'Rashid Khan',kind:'caught'}},
    match_state: {score:'100/4',over:'14.0',target:null},
    deltas: [{player:'Rashid Khan',final_points:-2},{player:'M Pathirana',final_points:25},{player:'RD Gaikwad',final_points:8}],
    team_total_after:200,tag:'wicket',
  }, {xi:['Rashid Khan','M Pathirana','RD Gaikwad'],captain:'M Pathirana',vice_captain:'RD Gaikwad'});
  expect(facts.team_points_delta).toBe('+31');
  expect(facts.breakdown).toEqual([
    {player:'Rashid Khan',points:-2,role:'regular'},
    {player:'M Pathirana',points:25,role:'captain'},
    {player:'RD Gaikwad',points:8,role:'vice-captain'},
  ]);
});

test('includes selected bowler with zero points on a captain boundary', () => {
  const facts = narrationFacts({event:{batter:'RA Jadeja',bowler:'MM Sharma',runs_batter:6,wicket:null},match_state:{score:'167/5',over:'14.5',target:171},deltas:[{player:'RA Jadeja',final_points:16}],team_total_after:713,tag:'boundary'}, {xi:['RA Jadeja','MM Sharma'],captain:'RA Jadeja',vice_captain:'MM Sharma'});
  expect(facts.breakdown).toContainEqual({player:'MM Sharma',points:0,role:'vice-captain'});
});
