import"./CWj6FrbW.js";import{i as ft}from"./cltGXJI8.js";import{ax as _t,aI as yt,ay as m,aE as s,aF as bt,s as h,o as R,az as e,a as r,aB as t,aG as M,aH as U,aA as o,ai as W,aC as g,aD as q}from"./CSAOJycW.js";import{i as T}from"./Y7iWmUx6.js";import{e as wt,i as Dt}from"./BdgDEE5z.js";import{s as St}from"./BMW2lFGB.js";import{g as Ft}from"./CHP0iK0l.js";import{t as kt}from"./M1FplM2V.js";import{g as E,l as N,k as Ct,m as $}from"./CN22JHGO.js";import{u as Ht}from"./IeG3TtpN.js";import{a as At}from"./DIRHbezi.js";var Rt=m('<section class="state-panel glass-card svelte-xe62gi"><p class="svelte-xe62gi">Loading training history...</p></section>'),Tt=m('<section class="state-panel glass-card svelte-xe62gi"><h2 class="svelte-xe62gi">Training history unavailable</h2> <p class="svelte-xe62gi"> </p></section>'),Et=m('<section class="state-panel glass-card svelte-xe62gi"><h2 class="svelte-xe62gi">No sessions yet</h2> <p class="svelte-xe62gi">Once you complete training sessions, they will appear here in a compact timeline.</p></section>'),Nt=m('<article class="history-row svelte-xe62gi"><div class="history-main"><p class="row-domain svelte-xe62gi"> </p> <p class="row-date svelte-xe62gi"> </p></div> <div class="history-metrics svelte-xe62gi"><div><p class="metric-label svelte-xe62gi">Score</p> <p class="metric-value svelte-xe62gi"> </p></div> <div><p class="metric-label svelte-xe62gi">Accuracy</p> <p class="metric-value svelte-xe62gi"> </p></div> <div><p class="metric-label svelte-xe62gi">Duration</p> <p class="metric-value svelte-xe62gi"> </p></div></div></article>'),$t=m('<section class="glass-card list-shell svelte-xe62gi"><div class="list-head svelte-xe62gi"><div><p class="card-label svelte-xe62gi">Training History</p> <h2 class="svelte-xe62gi">Recent sessions</h2></div> <div class="list-actions svelte-xe62gi"><p class="list-note svelte-xe62gi">A compact record of your recent training sessions.</p> <div class="action-row svelte-xe62gi"><button class="action-btn svelte-xe62gi">PDF Report</button> <button class="action-btn svelte-xe62gi">CSV Export</button></div></div></div> <div class="history-list svelte-xe62gi"></div></section>'),Bt=m('<div class="progress-panel"><!></div>');function qt(J,K){_t(K,!1);let _=null,y=R(!0),x=R(null),l=R([]);Ht.subscribe(i=>{_=i}),yt(async()=>{if(!_){Ft("/login");return}await Q()});async function Q(){h(y,!0),h(x,null);try{h(l,await kt.getHistory(_.id,30))}catch(i){console.error("Error loading training history:",i),h(x,"Complete more training sessions to review history.")}finally{h(y,!1)}}function X(){if(!r(l).length)return;const i=r(l).map(a=>({date:N(a.created_at),domain:E(a.domain),score:a.score.toFixed(1),accuracy:a.accuracy.toFixed(1),duration:$(a.duration)}));At(i,`training-history-${new Date().toISOString().split("T")[0]}`)}function Y(){if(!r(l).length||typeof window>"u")return;const i=r(l).map(c=>`
					<tr>
						<td>${N(c.created_at)}</td>
						<td>${E(c.domain)}</td>
						<td>${c.score.toFixed(1)}</td>
						<td>${c.accuracy.toFixed(1)}%</td>
						<td>${$(c.duration)}</td>
					</tr>`).join(""),a=window.open("","_blank","width=900,height=700");a&&(a.document.write(`
			<html>
				<head>
					<title>NeuroBloom Training History Report</title>
					<style>
						body { font-family: Arial, sans-serif; padding: 24px; color: #1f2937; }
						h1 { margin-bottom: 8px; }
						p { color: #475569; }
						table { width: 100%; border-collapse: collapse; margin-top: 20px; }
						th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; }
						th { background: #eef2ff; }
					</style>
				</head>
				<body>
					<h1>NeuroBloom Training History</h1>
					<p>Generated on ${new Date().toLocaleString()}</p>
					<table>
						<thead>
							<tr>
								<th>Date</th>
								<th>Domain</th>
								<th>Score</th>
								<th>Accuracy</th>
								<th>Duration</th>
							</tr>
						</thead>
						<tbody>${i}</tbody>
					</table>
				</body>
			</html>
		`),a.document.close(),a.focus(),a.print())}ft();var b=Bt(),Z=e(b);{var tt=i=>{var a=Rt();s(i,a)},et=i=>{var a=M(),c=U(a);{var at=n=>{var d=Tt(),f=o(e(d),2),w=e(f,!0);t(f),t(d),W(()=>g(w,r(x))),s(n,d)},rt=n=>{var d=M(),f=U(d);{var w=v=>{var u=Et();s(v,u)},it=v=>{var u=$t(),D=e(u),B=o(e(D),2),G=o(e(B),2),I=e(G),ot=o(I,2);t(G),t(B),t(D);var L=o(D,2);wt(L,5,()=>r(l),Dt,(st,p)=>{var S=Nt(),F=e(S),k=e(F),lt=e(k,!0);t(k);var O=o(k,2),ct=e(O,!0);t(O),t(F);var P=o(F,2),C=e(P),H=o(e(C),2),nt=e(H,!0);t(H),t(C);var A=o(C,2),V=o(e(A),2),dt=e(V);t(V),t(A);var j=o(A,2),z=o(e(j),2),vt=e(z,!0);t(z),t(j),t(P),t(S),W((pt,gt,mt,ut,ht,xt)=>{g(lt,pt),g(ct,gt),St(H,`color: ${mt??""}`),g(nt,ut),g(dt,`${ht??""}%`),g(vt,xt)},[()=>E(r(p).domain),()=>N(r(p).created_at),()=>Ct(r(p).score),()=>r(p).score.toFixed(1),()=>r(p).accuracy.toFixed(1),()=>$(r(p).duration)]),s(st,S)}),t(L),t(u),q("click",I,Y),q("click",ot,X),s(v,u)};T(f,v=>{r(l).length===0?v(w):v(it,!1)},!0)}s(n,d)};T(c,n=>{r(x)?n(at):n(rt,!1)},!0)}s(i,a)};T(Z,i=>{r(y)?i(tt):i(et,!1)})}t(b),s(J,b),bt()}export{qt as component};
