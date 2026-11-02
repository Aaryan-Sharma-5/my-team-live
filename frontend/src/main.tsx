import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
import {nextPlayback} from './playback';
import {Feed} from './Feed';
import {Sparkline} from './Sparkline';
import {TeamSetup} from './TeamSetup';
import {change, fmt, isKey, Narration, Replay, shortName, Team} from './types';

type Outcome={winner:string;by:{wickets?:number;runs?:number};method?:string};
async function get(path:string) {
  const deadline=Date.now()+60000;
  while(Date.now()<deadline){try{const r=await fetch('/api/'+path,{signal:AbortSignal.timeout(Math.min(10000,Math.max(1,deadline-Date.now())))});if(r.ok)return await r.json()}catch{} if(Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,Math.min(2000,deadline-Date.now())))}
  throw Error('Could not load '+path);
}
const sameTeam=(a:Team,b:Team)=>a.captain===b.captain&&a.vice_captain===b.vice_captain&&a.xi.length===b.xi.length&&a.xi.every(p=>b.xi.includes(p));
const ruleLabels:Record<string,string>={run:'Run',four_bonus:'Four bonus',six_bonus:'Six bonus','30_runs':'30-run bonus','50_runs':'50-run bonus','100_runs':'100-run bonus',duck:'Duck',wicket:'Bowler wicket',bowled_lbw_bonus:'Bowled/LBW bonus','3_wickets':'3-wicket haul','5_wickets':'5-wicket haul',catch:'Catch',run_out:'Run out',captain_multiplier:'Captain ×',vice_captain_multiplier:'Vice-captain ×'};

function App(){
  const [team,setTeam]=useState<Team|null>(null);const [defaultTeam,setDefaultTeam]=useState<Team|null>(null);
  const [rules,setRules]=useState<Record<string,number>>({});const [pool,setPool]=useState<string[]>([]);const [outcome,setOutcome]=useState<Outcome|null>(null);
  const [replay,setReplay]=useState<Replay|null>(null);const [idx,setIdx]=useState(-1);const [running,setRunning]=useState(false);const [speed,setSpeed]=useState(30);const [error,setError]=useState('');
  const [aiConfigured,setAiConfigured]=useState(false);const [narrations,setNarrations]=useState<Record<number,Narration>>({});const requested=useRef(new Set<number>());
  useEffect(()=>{Promise.all([get('default-team'),get('rules'),get('match')]).then(([t,r,m])=>{setTeam(t);setDefaultTeam(t);setRules(r);setPool(Object.values(m.players as Record<string,string[]>).flat());setOutcome(m.outcome)}).catch(()=>setError('Replay could not load. Please refresh to try again.'))},[]);
  useEffect(()=>{get('health').then(h=>setAiConfigured(h.ai_configured)).catch(()=>setAiConfigured(false))},[]);
  useEffect(()=>{if(!running||!replay)return;const id=setInterval(()=>setIdx(i=>{if(i>=replay.items.length-1){setRunning(false);return i}return i+1}),10000/speed);return()=>clearInterval(id)},[running,replay,speed]);
  useEffect(()=>{
    if(!aiConfigured||!replay||!team||!defaultTeam||sameTeam(team,defaultTeam))return;
    const eligible=new Set(['boundary','wicket','milestone','captain','danger','mixed']);
    for(const i of replay.items.slice(Math.max(0,idx),Math.max(0,idx)+8)){
      if(!i.relevant||!eligible.has(i.tag)||!change(i)||requested.current.has(i.seq))continue;
      requested.current.add(i.seq);
      fetch('/api/narrate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({team,seq:i.seq})}).then(r=>r.ok?r.json():Promise.reject()).then(result=>setNarrations(old=>({...old,[i.seq]:result}))).catch(()=>{});
    }
  },[idx,replay,team,defaultTeam,aiConfigured]);
  async function start(){
    if(!team)return;setError('');
    try{const r=await fetch('/api/replay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(team)});if(!r.ok)throw Error();const timeline:Replay=await r.json();requested.current.clear();setNarrations(Object.fromEntries(timeline.items.filter(i=>i.narration).map(i=>[i.seq,i.narration!])));setReplay(timeline);setIdx(-1);setRunning(true)}catch{setError('Could not start replay. Please try again.')}
  }
  const item=idx>=0?replay?.items[idx]:undefined;const played=replay?.items.slice(0,idx+1)??[];
  const totals=item?.player_totals_after??Object.fromEntries((team?.xi??[]).map(p=>[p,0]));
  const sorted=Object.entries(totals).sort((a,b)=>b[1]-a[1]);const maxPlayer=Math.max(1,...sorted.map(([,n])=>n));
  const remainingBalls=90-played.filter(i=>i.match_state.innings===2&&!['wide','noball'].includes(i.event.extra_type??'')).length;
  const needed=item?.match_state.target?Math.max(0,item.match_state.target-Number(item.match_state.score.split('/')[0])):0;
  const finished=!!replay&&idx>=replay.items.length-1;const diff=item?change(item):0;
  const nextMoment=()=>{if(!replay)return;const next=replay.items.findIndex((i,k)=>k>idx&&isKey(i));if(next>=0)setIdx(next)};
  return <div className="shell"><header><div className="brand"><span className="mark">M</span><div><strong>MY TEAM <span>LIVE</span></strong><small>YOUR MATCH. YOUR MOMENTS.</small></div></div><span className="badge">● MATCH REPLAY</span></header>
    <main className={replay?'playing':''}><div className="hero"><div className="eyebrow">IPL 2023 FINAL <span> / </span> 29 MAY 2023</div><h1>Every ball has a story.<br/><em>Here’s yours.</em></h1><p className="intro">Your fantasy XI, right in the middle of the action. Follow the moments that move your points.</p><div className="matchline"><span>GUJARAT TITANS <b>vs</b> CHENNAI SUPER KINGS</span><span>SIMPLIFIED SCORING · NOT LIVE</span></div></div>
      {error&&<div className="error" role="alert">{error}</div>}
      {!replay?<TeamSetup team={team} pool={pool} onTeam={setTeam} onStart={start}/>:<>
        <div className="score-sticky"><section className="scoregrid"><div className="panel score"><span className="label">MY TEAM POINTS</span><div className={`big ${diff>0?'score-gain':diff<0?'score-loss':''}`} key={diff?idx:'steady'}>{fmt(item?.team_total_after??0)}<small> PTS</small></div><p>Top scorer <strong>{sorted[0]?.[1]?shortName(sorted[0][0]):'—'}</strong></p></div><div className="panel matchscore"><span className="label">MATCH SCORE · INNINGS {item?.match_state.innings??1}</span><div className="big">{item?.match_state.score??'0/0'}<small> / {item?.match_state.over??'0.0'} OV</small></div><p>{finished&&outcome?`${outcome.winner} won by ${outcome.by.wickets??outcome.by.runs} ${outcome.by.wickets?'wickets':'runs'}${outcome.method?' (DLS)':''}`:item?.match_state.target?`Target ${item.match_state.target} · ${needed} needed from ${Math.max(0,remainingBalls)} balls${remainingBalls>0?` · RRR ${(needed*6/remainingBalls).toFixed(1)}`:''}`:'Gujarat Titans batting'}</p></div></section></div>
        {item?.tag==='danger'&&<div className="danger" role="status">KEY PLAYER OUT · {shortName(item.event.wicket?.player_out??'')} is dismissed.</div>}
        <div className="controls panel"><button onClick={()=>{const n=nextPlayback(idx,replay.items.length-1,running);setIdx(n.index);setRunning(n.running)}}>{finished?'↺ Replay':running?'Ⅱ Pause':'▶ Play'}</button><button onClick={()=>{setIdx(-1);setRunning(true)}}>↺ Restart</button><button onClick={nextMoment} disabled={finished}>Next key moment →</button><label>Speed <select value={speed} onChange={e=>setSpeed(Number(e.target.value))}>{[1,5,10,30].map(n=><option key={n} value={n}>{n}×</option>)}</select></label><span>{idx+1} / {replay.items.length} deliveries</span></div>
        {finished&&<div className="panel finish"><span className="eyebrow">FULL TIME</span><h2>Your team finished on {fmt(replay.final.team_total)} points.</h2><p>Top contributors: {sorted.slice(0,3).map(([p,n])=>`${shortName(p)} (${fmt(n)})`).join(', ')}. Captain share: {replay.final.team_total?Math.round((totals[team!.captain]||0)/replay.final.team_total*100):0}%.</p></div>}
        <Sparkline items={replay.items} index={idx}/>
        <div className="columns"><Feed played={played} team={team!} narrations={narrations} finished={finished}/><aside><div className="titleline"><div><span className="eyebrow">YOUR LINEUP</span><h2>Player points</h2></div></div><div className="panel breakdown">{sorted.map(([p,n])=><details key={p}><summary><span>{shortName(p)} {team?.captain===p?<b className="role-chip">C</b>:team?.vice_captain===p?<b className="role-chip">VC</b>:null}</span><strong>{fmt(n)}</strong></summary><div className="bar-track" aria-hidden="true"><div style={{width:`${Math.max(0,n)/maxPlayer*100}%`}}/></div><div className="calcs">{played.flatMap(i=>i.deltas.filter(d=>d.player===p).map(d=>({d,event:i}))).map(({d,event},i)=><div key={i}>Innings {event.match_state.innings} · {event.match_state.over} ov · {d.reason_text}: {d.final_points>0?'+':''}{fmt(d.final_points)}</div>)}</div></details>)}</div><details className="panel rules"><summary>Scoring rules <span>＋</span></summary><p>Demonstration scoring, not official Dream11 points.</p>{Object.entries(rules).map(([k,v])=><div key={k}><span>{ruleLabels[k]??k.replaceAll('_',' ')}</span><b>{v}</b></div>)}</details></aside></div>
      </>}
    </main><footer>CRICSHEET 1370353 · NARENDRA MODI STADIUM, AHMEDABAD<br/>A MATCH REPLAY WITH SIMPLIFIED SCORING. NOT AFFILIATED WITH DREAM11.</footer>
  </div>
}
createRoot(document.getElementById('root')!).render(<App/>);
