import {expect,test} from 'vitest';
import {rows} from './Feed';
import {isKey,Item} from './types';

const item=(seq:number,tag:string,over:number,points:number):Item=>({seq,tag,relevant:true,event:{over,batter:'A',bowler:'B',runs_batter:1,extra_type:null,wicket:null},match_state:{innings:1,over:`${over}.1`,score:'1/0',target:null},deltas:[{player:'A',reason_text:'run',base_points:points,multiplier:1,final_points:points}],player_totals_after:{A:points},team_total_after:points,template_text:''});

test('only meaningful captain plays join key moments',()=>{
  expect(isKey(item(1,'captain',0,2))).toBe(false);
  expect(isKey(item(2,'captain',0,8))).toBe(true);
  expect(isKey(item(3,'mixed',0,50))).toBe(true);
});

test('run summaries stop at boundaries and over changes',()=>{
  const result=rows([item(0,'run',0,1),item(1,'run',0,2),item(2,'boundary',0,5),item(3,'run',1,1)]);
  expect(result.map(r=>r.kind)).toEqual(['runs','event','runs']);
  expect(result.at(-1)).toMatchObject({kind:'runs',items:[{seq:0},{seq:1}]});
});
