import React, {useEffect, useRef, useState} from 'react';
import {shortName, Team} from './types';

export function TeamSetup({team,pool,onTeam,onStart}:{team:Team|null;pool:string[];onTeam:(t:Team)=>void;onStart:()=>void}) {
  const [swapping,setSwapping]=useState<string|null>(null);
  const closeRef=useRef<HTMLButtonElement>(null);
  useEffect(()=>{if(swapping) closeRef.current?.focus()},[swapping]);
  function role(player:string,kind:'captain'|'vice_captain') {
    if(!team)return;
    const other=kind==='captain'?'vice_captain':'captain';
    onTeam({...team,[kind]:player,[other]:team[other]===player?team[kind]:team[other]});
  }
  function swap(player:string){
    if(!team||!swapping)return;
    onTeam({...team,xi:team.xi.map(p=>p===swapping?player:p),captain:team.captain===swapping?player:team.captain,vice_captain:team.vice_captain===swapping?player:team.vice_captain});
    setSwapping(null);
  }
  return <section className="setup panel"><div className="sectionhead"><div><span className="eyebrow">READY TO PLAY</span><h2>Your XI is set.</h2><p>{team?'We picked a team to get you straight into the match.':'The replay is warming up. This can take a minute.'}</p></div><button className="primary" onClick={onStart} disabled={!team}>Start replay <span>→</span></button></div>
    <div className="tip">Tap a player to swap. Choose your C and VC.</div><div className="players">{team?.xi.map(p=><div className="player" key={p}><button className="swap-player" onClick={()=>setSwapping(p)} aria-label={`Swap ${p}`}><span>{shortName(p)}</span><span className="swap-hint">SWAP ↗</span></button><div><button className={team.captain===p?'selected':''} onClick={()=>role(p,'captain')} aria-label={`Set ${p} as captain`}>C</button><button className={team.vice_captain===p?'selected':''} onClick={()=>role(p,'vice_captain')} aria-label={`Set ${p} as vice-captain`}>VC</button></div></div>)}</div>
    {swapping&&<div className="sheet-backdrop" onClick={()=>setSwapping(null)}><div role="dialog" aria-modal="true" aria-label={`Swap ${swapping}`} className="swap-sheet" onClick={e=>e.stopPropagation()} onKeyDown={e=>{if(e.key==='Escape')setSwapping(null)}}><div className="sheet-head"><div><span className="eyebrow">CHANGE YOUR XI</span><h2>Swap {shortName(swapping)}</h2></div><button ref={closeRef} className="sheet-close" onClick={()=>setSwapping(null)} aria-label="Close swap options">✕</button></div><p>Choose a player from this match.</p><div className="swap-options">{pool.filter(p=>!team?.xi.includes(p)).map(p=><button key={p} onClick={()=>swap(p)}>{p} <span>＋</span></button>)}</div></div></div>}
  </section>
}
