import { h as head, s as store_get, u as unsubscribe_stores } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import "../../../../../chunks/api.js";
import "../../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../../chunks/TaskPracticeActions.js";
import { a as localeText, l as locale } from "../../../../../chunks/index3.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let totalTrials = 60;
    let practiceStatusMessage = "";
    user.subscribe((value) => {
      if (!value) goto();
    });
    head("1aegwe3", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Attention Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="cpt-container svelte-1aegwe3" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="page-content svelte-1aegwe3"><div class="task-header svelte-1aegwe3"><button class="back-btn svelte-1aegwe3">${escape_html("Back to Dashboard")}</button> <h1 class="task-title svelte-1aegwe3">Continuous Performance Test</h1></div> <div class="concept-card svelte-1aegwe3"><div class="concept-badge svelte-1aegwe3">Attention · Baseline Assessment</div> <h2 class="svelte-1aegwe3">What This Test Measures</h2> <p class="svelte-1aegwe3">The CPT measures <strong>sustained attention</strong> — your ability to stay vigilant and respond selectively over an extended period. You will watch a rapid stream of letters and respond only to a specific two-letter sequence. The test distinguishes genuine target detections from impulsive false alarms and tracks whether attention declines over time.</p></div> <div class="rules-card svelte-1aegwe3"><h3 class="svelte-1aegwe3">AX Rule</h3> <div class="ax-example svelte-1aegwe3"><div class="ax-slot ax-other svelte-1aegwe3">B</div> <div class="ax-arrow svelte-1aegwe3">→</div> <div class="ax-slot ax-a svelte-1aegwe3">A</div> <div class="ax-arrow svelte-1aegwe3">→</div> <div class="ax-slot ax-x svelte-1aegwe3">X</div> <div class="ax-respond svelte-1aegwe3">Click here</div></div> <ul class="rules-list svelte-1aegwe3"><li class="svelte-1aegwe3">Letters appear <strong>one per second</strong> — stay alert</li> <li class="svelte-1aegwe3">Click <strong>only when X follows A</strong> (the A→X sequence)</li> <li class="svelte-1aegwe3">Do NOT click for X alone, A alone, or any other letter</li> <li class="svelte-1aegwe3">False clicks count as errors — accuracy matters as much as speed</li> <li class="svelte-1aegwe3">~${escape_html(totalTrials)} trials · approximately 1 minute</li></ul></div> <div class="examples-grid svelte-1aegwe3"><div class="example-card ex-correct svelte-1aegwe3"><div class="ex-tag svelte-1aegwe3">Click</div> <div class="ex-seq svelte-1aegwe3"><span class="ex-a svelte-1aegwe3">A</span> → <span class="ex-x svelte-1aegwe3">X</span></div> <div class="ex-note svelte-1aegwe3">A immediately before X</div></div> <div class="example-card ex-wrong svelte-1aegwe3"><div class="ex-tag svelte-1aegwe3">Do NOT click</div> <div class="ex-seq svelte-1aegwe3"><span class="ex-a svelte-1aegwe3">A</span> → <span class="ex-b svelte-1aegwe3">B</span> → <span class="ex-x svelte-1aegwe3">X</span></div> <div class="ex-note svelte-1aegwe3">A was not the one right before X</div></div> <div class="example-card ex-wrong svelte-1aegwe3"><div class="ex-tag svelte-1aegwe3">Do NOT click</div> <div class="ex-seq svelte-1aegwe3"><span class="ex-b svelte-1aegwe3">B</span> → <span class="ex-x svelte-1aegwe3">X</span></div> <div class="ex-note svelte-1aegwe3">Preceding letter was not A</div></div></div> <div class="tip-card svelte-1aegwe3"><div class="tip-title svelte-1aegwe3">Strategy</div> <p class="svelte-1aegwe3">Focus on remembering the previous letter, not the current one. When you see any letter, your job is to decide: "was the last letter A?" If yes, wait for the next letter — if it is X, click. Avoid the temptation to click whenever you see X.</p></div> <div class="clinical-card svelte-1aegwe3"><h3 class="svelte-1aegwe3">Clinical Basis</h3> <p class="svelte-1aegwe3">Sustained attention deficits affect over 50% of people with MS, even in early stages. The CPT (AX variant) is sensitive to fronto-parietal white matter disruption. Two key metrics — hit rate and false alarm rate — can be combined into a d' (d-prime) sensitivity index, which is used in the Brief International Cognitive Assessment for MS (BICAMS) and other MS-specific batteries. Vigilance decrement (performance drop in the second half) reflects fatigue-driven attention failure, a distinctive feature of MS cognitive impairment.</p></div> `);
      TaskPracticeActions($$renderer2, {
        locale: store_get($$store_subs ??= {}, "$locale", locale),
        startLabel: localeText({ en: "Start Actual Test", bn: "আসল পরীক্ষা শুরু করুন" }, store_get($$store_subs ??= {}, "$locale", locale)),
        statusMessage: practiceStatusMessage
      });
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
