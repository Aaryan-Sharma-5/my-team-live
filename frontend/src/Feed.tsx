import React, {useEffect, useMemo, useState} from 'react';
import {change, fmt, isKey, Item, Narration, shortName, signed, Team} from './types';

type Filter = 'key'|'all'|'captain'|'wickets';
type Row = {kind:'event';item:Item}|{kind:'runs';items:Item[]};
const wicket = (item:Item) => !!item.event.wicket;
const plainRun = (item:Item) => item.tag==='run' || (item.tag==='captain' && !item.event.wicket && Math.abs(change(item))<5);
export function rows(items:Item[]):Row[] {
  const grouped:Row[]=[];
  for(const item of items){
    const last=grouped.at(-1);
    // The over containing a delivery is zero-indexed by its source event.
    const over=item.event.over;
    if(plainRun(item) && last?.kind==='runs'){
      const previous=last.items.at(-1)!;
      const prevOver=previous.event.over;
      if(previous.match_state.innings===item.match_state.innings && prevOver===over){last.items.push(item);continue}
    }
    grouped.push(plainRun(item)?{kind:'runs',items:[item]}:{kind:'event',item});
  }
  return grouped.reverse();
}
function textFor(item:Item, narration?:Narration){
  let text=narration?.text??item.template_text;
  const names=new Set([item.event.batter,item.event.bowler,item.event.wicket?.player_out,...item.deltas.map(d=>d.player)]);
  for(const name of names)if(name)text=text.split(name).join(shortName(name));
  return text.replace(/\b1 points\b/g,'1 point');
}
function calc(item:Item){
  const grouped = new Map<string,typeof item.deltas>();
  for(const d of item.deltas)grouped.set(d.player,[...(grouped.get(d.player)??[]),d]);
  return [...grouped].map(([p,ds])=>{const base=ds.reduce((n,d)=>n+d.base_points,0);const total=ds.reduce((n,d)=>n+d.final_points,0);const desc=ds.map(d=>d.reason_text).join(' + ');return <div key={p}><b>{shortName(p)}</b> · {desc}: {signed(base)}{ds[0].multiplier!==1?` × ${ds[0].multiplier} = ${signed(total)}`:''}</div>});
}
export function EventCard({item,narration,spotlight=false}:{item:Item;narration?:Narration;spotlight?:boolean}) {
  const amount=change(item);const mixed=item.tag==='mixed';
  return <article className={`panel card ${spotlight?'spotlight':''} ${mixed?'mixed-card':''}`}><div className="cardtop"><span>INN {item.match_state.innings} · {item.match_state.over} OV <b> / {mixed?'MIXED MOMENT':item.tag.toUpperCase()}</b></span><strong className={mixed?'mixed-chip':amount<0?'negative':'positive'}>{signed(amount)} PTS</strong></div><h3>{item.event.wicket?`${shortName(item.event.wicket.player_out)} · ${item.event.wicket.kind}`:`${shortName(item.event.batter)} · ${item.event.runs_batter} ${item.event.runs_batter===1?'run':'runs'}`}</h3><p>{textFor(item,narration)} <span className="source">{narration?.source==='ai-pre-generated'?'AI (PRE-GENERATED)':narration?.source==='ai'?'AI':'TEMPLATE'}</span></p><div className="calcs">{calc(item)}</div></article>
}
export function Feed({played,team,narrations,finished}:{played:Item[];team:Team;narrations:Record<number,Narration>;finished:boolean}) {
  const [filter,setFilter]=useState<Filter>('key');
  useEffect(()=>{if(finished)setFilter('key')},[finished]);
  const relevant=played.filter(i=>i.relevant);
  const matching=relevant.filter(i=>filter==='all'||filter==='key'&&isKey(i)||filter==='wickets'&&wicket(i)||filter==='captain'&&(i.deltas.some(d=>d.player===team.captain)||i.event.wicket?.player_out===team.captain));
  const ranked=useMemo(()=>[...relevant].filter(isKey).sort((a,b)=>{
    const score=(i:Item)=>Math.abs(change(i))+(i.tag==='mixed'?20:0)+(i.seq>=played.length-10?30:0);
    return score(b)-score(a)||b.seq-a.seq;
  }).slice(0,5).sort((a,b)=>a.seq-b.seq),[played]);
  const displayed=finished&&filter==='key'?rows(ranked):rows(matching).slice(0,30);
  const spotlight=[...relevant].reverse().find(isKey);
  return <section className="feed-section">{spotlight&&!finished&&<><div className="titleline"><div><span className="eyebrow">RIGHT NOW</span><h2>Your spotlight</h2></div></div><EventCard item={spotlight} narration={narrations[spotlight.seq]} spotlight/></>}
    <div className="titleline feed-title"><div><span className="eyebrow">THE MOMENTS THAT MATTER</span><h2>{finished&&filter==='key'?'Top five moments':'Your match feed'}</h2></div><span className="count">{matching.length} UPDATES</span></div>
    <div className="filter-row" role="group" aria-label="Filter match feed">{([['key','Key moments'],['all','All'],['captain','Captain'],['wickets','Wickets']] as const).map(([v,label])=><button key={v} className={filter===v?'active':''} aria-pressed={filter===v} onClick={()=>setFilter(v)}>{label}</button>)}</div>
    {displayed.length===0&&<div className="panel empty">No moments here yet. Your updates will appear as the match plays.</div>}
    {displayed.map(row=>row.kind==='event'?<EventCard key={row.item.seq} item={row.item} narration={narrations[row.item.seq]}/>:row.items.length===1?<EventCard key={row.items[0].seq} item={row.items[0]} narration={narrations[row.items[0].seq]}/>:<div className="panel run-summary" key={row.items[0].seq}><span>INN {row.items[0].match_state.innings} · OVER {row.items[0].event.over+1}</span><p>{row.items.length} scoring balls · {signed(row.items.reduce((n,i)=>n+change(i),0))} team points</p></div>)}
    {matching.length>30&&!(finished&&filter==='key')&&<p className="feed-limit">Showing the latest 30 rows.</p>}
  </section>
}
