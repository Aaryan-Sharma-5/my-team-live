import React from 'react';
import {Item, isKey} from './types';

export function Sparkline({items,index}:{items:Item[];index:number}) {
  const points=items.slice(0,index+1); const max=Math.max(1,...points.map(i=>i.team_total_after)); const min=Math.min(0,...points.map(i=>i.team_total_after));
  const x=(seq:number)=>points.length>1?(seq/(items.length-1))*296+2:2;
  const y=(score:number)=>62-(score-min)/(max-min)*54;
  const line=points.map((p,k)=>`${x(k)},${y(p.team_total_after)}`).join(' ');
  const markers=points.filter(i=>isKey(i)&& (i.tag==='mixed'||i.tag==='wicket'||i.tag==='danger'||Math.abs(i.deltas.reduce((s,d)=>s+d.final_points,0))>=15));
  return <div className="graph panel"><div className="graph-head"><div><span className="eyebrow">YOUR POINTS JOURNEY</span><h2>Every moment adds up.</h2></div><span className="graph-caption">MATCH PROGRESS</span></div><svg viewBox="0 0 300 68" role="img" aria-label={`Your team points over the match so far: ${points.at(-1)?.team_total_after??0}`} preserveAspectRatio="none"><line x1="2" y1="62" x2="298" y2="62" className="graph-grid"/><line x1="2" y1="34" x2="298" y2="34" className="graph-grid"/><polyline points={line} fill="none" className="graph-line"/>{markers.map(m=><circle key={m.seq} cx={x(m.seq)} cy={y(m.team_total_after)} r="2.8" className={m.tag==='mixed'?'mixed-dot':'graph-dot'}/>)}</svg><div className="graph-axis"><span>START</span><span>1ST INNINGS</span><span>FINISH</span></div><div className="graph-events">{([[41,"Gill stumped"],[118,"Sudharsan out"],[215,"Jadeja finish"]] as const).filter(([seq])=>seq<=index&&items[seq]?.relevant).map(([seq,label])=><span key={seq}>● {label} · {items[seq].team_total_after} pts</span>)}</div></div>
}
