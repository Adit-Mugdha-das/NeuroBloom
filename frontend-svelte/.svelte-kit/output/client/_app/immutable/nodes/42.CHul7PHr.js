import{f as m,a as i,c as U,s as h,e as W}from"../chunks/D0ceBE4O.js";import{i as gt}from"../chunks/BtBcnEEO.js";import{p as _t,at as yt,a as bt,b as u,m as T,c as a,g as r,r as t,f as q,s,t as z}from"../chunks/B_svR1Ec.js";import{i as A}from"../chunks/Ky5-2dZi.js";import{e as wt,i as xt}from"../chunks/DKn0IgOT.js";import{s as Dt}from"../chunks/Dwclz_Xk.js";import{g as St}from"../chunks/Ckn0ZsGu.js";import{c as Ft}from"../chunks/B7kakw_8.js";import{a as N,f as $,c as Ct,e as E}from"../chunks/BTLARRCp.js";import{u as Ht}from"../chunks/D7E9gqHK.js";import{a as Rt}from"../chunks/DIRHbezi.js";var Tt=m('<section class="state-panel glass-card svelte-hn5kk5"><p class="svelte-hn5kk5">Loading training history...</p></section>'),At=m('<section class="state-panel glass-card svelte-hn5kk5"><h2 class="svelte-hn5kk5">Training history unavailable</h2> <p class="svelte-hn5kk5"> </p></section>'),Nt=m('<section class="state-panel glass-card svelte-hn5kk5"><h2 class="svelte-hn5kk5">No sessions yet</h2> <p class="svelte-hn5kk5">Once you complete training sessions, they will appear here in a compact timeline.</p></section>'),$t=m('<article class="history-row svelte-hn5kk5"><div class="history-main"><p class="row-domain svelte-hn5kk5"> </p> <p class="row-date svelte-hn5kk5"> </p></div> <div class="history-metrics svelte-hn5kk5"><div><p class="metric-label svelte-hn5kk5">Score</p> <p class="metric-value svelte-hn5kk5"> </p></div> <div><p class="metric-label svelte-hn5kk5">Accuracy</p> <p class="metric-value svelte-hn5kk5"> </p></div> <div><p class="metric-label svelte-hn5kk5">Duration</p> <p class="metric-value svelte-hn5kk5"> </p></div></div></article>'),Et=m('<section class="glass-card list-shell svelte-hn5kk5"><div class="list-head svelte-hn5kk5"><div><p class="card-label svelte-hn5kk5">Training History</p> <h2 class="svelte-hn5kk5">Recent sessions</h2></div> <div class="list-actions svelte-hn5kk5"><p class="list-note svelte-hn5kk5">A compact record of your recent training sessions.</p> <div class="action-row svelte-hn5kk5"><button class="action-btn svelte-hn5kk5">PDF Report</button> <button class="action-btn svelte-hn5kk5">CSV Export</button></div></div></div> <div class="history-list svelte-hn5kk5"></div></section>'),Bt=m('<div class="progress-panel"><!></div>');function zt(J,K){_t(K,!1);let _=null,y=T(!0),f=T(null),l=T([]);Ht.subscribe(o=>{_=o}),yt(async()=>{if(!_){St("/login");return}await Q()});async function Q(){u(y,!0),u(f,null);try{u(l,await Ft.getHistory(_.id,30))}catch(o){console.error("Error loading training history:",o),u(f,"Complete more training sessions to review history.")}finally{u(y,!1)}}function X(){if(!r(l).length)return;const o=r(l).map(e=>({date:$(e.created_at),domain:N(e.domain),score:e.score.toFixed(1),accuracy:e.accuracy.toFixed(1),duration:E(e.duration)}));Rt(o,`training-history-${new Date().toISOString().split("T")[0]}`)}function Y(){if(!r(l).length||typeof window>"u")return;const o=r(l).map(n=>`
					<tr>
						<td>${$(n.created_at)}</td>
						<td>${N(n.domain)}</td>
						<td>${n.score.toFixed(1)}</td>
						<td>${n.accuracy.toFixed(1)}%</td>
						<td>${E(n.duration)}</td>
					</tr>`).join(""),e=window.open("","_blank","width=900,height=700");e&&(e.document.write(`
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
						<tbody>${o}</tbody>
					</table>
				</body>
			</html>
		`),e.document.close(),e.focus(),e.print())}gt();var b=Bt(),Z=a(b);{var tt=o=>{var e=Tt();i(o,e)},at=o=>{var e=U(),n=q(e);{var et=c=>{var d=At(),g=s(a(d),2),w=a(g,!0);t(g),t(d),z(()=>h(w,r(f))),i(c,d)},rt=c=>{var d=U(),g=q(d);{var w=v=>{var k=Nt();i(v,k)},ot=v=>{var k=Et(),x=a(k),B=s(a(x),2),L=s(a(B),2),O=a(L),st=s(O,2);t(L),t(B),t(x);var P=s(x,2);wt(P,5,()=>r(l),xt,(it,p)=>{var D=$t(),S=a(D),F=a(S),lt=a(F,!0);t(F);var V=s(F,2),nt=a(V,!0);t(V),t(S);var j=s(S,2),C=a(j),H=s(a(C),2),ct=a(H,!0);t(H),t(C);var R=s(C,2),G=s(a(R),2),dt=a(G);t(G),t(R);var I=s(R,2),M=s(a(I),2),vt=a(M,!0);t(M),t(I),t(j),t(D),z((pt,ht,mt,kt,ut,ft)=>{h(lt,pt),h(nt,ht),Dt(H,`color: ${mt??""}`),h(ct,kt),h(dt,`${ut??""}%`),h(vt,ft)},[()=>N(r(p).domain),()=>$(r(p).created_at),()=>Ct(r(p).score),()=>r(p).score.toFixed(1),()=>r(p).accuracy.toFixed(1),()=>E(r(p).duration)]),i(it,D)}),t(P),t(k),W("click",O,Y),W("click",st,X),i(v,k)};A(g,v=>{r(l).length===0?v(w):v(ot,!1)},!0)}i(c,d)};A(n,c=>{r(f)?c(et):c(rt,!1)},!0)}i(o,e)};A(Z,o=>{r(y)?o(tt):o(at,!1)})}t(b),i(J,b),bt()}export{zt as component};
