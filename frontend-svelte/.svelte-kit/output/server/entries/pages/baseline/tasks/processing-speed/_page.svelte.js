import { h as head, s as store_get, u as unsubscribe_stores } from "../../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import "../../../../../chunks/api.js";
import "../../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../../chunks/TaskPracticeActions.js";
import { a as localeText, l as locale } from "../../../../../chunks/index3.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let practiceStatusMessage = "";
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    head("12u9kq2", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(lt("Processing Speed Test - NeuroBloom", "প্রসেসিং স্পিড টেস্ট - NeuroBloom"))}</title>`);
      });
    });
    $$renderer2.push(`<div class="ps-container svelte-12u9kq2" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="page-content svelte-12u9kq2"><div class="task-header svelte-12u9kq2"><button class="back-btn svelte-12u9kq2">${escape_html("Back to Dashboard")}</button> <h1 class="task-title svelte-12u9kq2">Simple Reaction Time</h1></div> <div class="concept-card svelte-12u9kq2"><div class="concept-badge svelte-12u9kq2">Processing Speed · Baseline Assessment</div> <h2 class="svelte-12u9kq2">What This Test Measures</h2> <p class="svelte-12u9kq2">This two-part test measures how quickly and accurately you can process and respond to visual stimuli. Part 1 isolates pure motor reaction speed; Part 2 adds a discrimination element that taxes both speed and decision-making simultaneously.</p></div> <div class="parts-grid svelte-12u9kq2"><div class="part-card part-1 svelte-12u9kq2"><div class="part-num svelte-12u9kq2">Part 1</div> <div class="part-title svelte-12u9kq2">Simple Reaction Time</div> <ul class="part-list svelte-12u9kq2"><li class="svelte-12u9kq2">The screen flashes <span class="green-tag svelte-12u9kq2">GREEN</span></li> <li class="svelte-12u9kq2">Click anywhere as fast as possible</li> <li class="svelte-12u9kq2">Do not click before the green flash</li> <li class="svelte-12u9kq2">${escape_html("—")} trials</li></ul></div> <div class="part-card part-2 svelte-12u9kq2"><div class="part-num svelte-12u9kq2">Part 2</div> <div class="part-title svelte-12u9kq2">Choice Reaction Time</div> <ul class="part-list svelte-12u9kq2"><li class="svelte-12u9kq2">A colored shape appears on screen</li> <li class="svelte-12u9kq2">Click the matching button as fast as possible</li> <li class="svelte-12u9kq2">Speed AND accuracy both matter</li> <li class="svelte-12u9kq2">${escape_html("—")} trials · ${escape_html(2)} shapes</li></ul></div></div> <div class="tip-card svelte-12u9kq2"><div class="tip-title svelte-12u9kq2">Strategy</div> <p class="svelte-12u9kq2">Stay relaxed with your hand already resting near the button. Tension slows reaction time. For Part 2, avoid guessing — a wrong click counts against your score as much as a slow correct one.</p> <div class="rt-scale svelte-12u9kq2"><span class="rts-label svelte-12u9kq2">Excellent</span> <span class="rts-range svelte-12u9kq2">&lt; 200ms</span> <span class="rts-sep svelte-12u9kq2">·</span> <span class="rts-label svelte-12u9kq2">Good</span> <span class="rts-range svelte-12u9kq2">200–300ms</span> <span class="rts-sep svelte-12u9kq2">·</span> <span class="rts-label svelte-12u9kq2">Average</span> <span class="rts-range svelte-12u9kq2">300–400ms</span></div></div> <div class="clinical-card svelte-12u9kq2"><h3 class="svelte-12u9kq2">Clinical Basis</h3> <p class="svelte-12u9kq2">Reaction time is one of the most reliably slowed measures in multiple sclerosis, reflecting demyelination-related slowing of neural conduction velocity. Simple reaction time assessments have been used in MS research since the 1980s and remain a key component of the Symbol Digit Modalities Test (SDMT) battery. Slowed processing speed affects up to 70% of MS patients and is the strongest predictor of employment status, driving safety, and everyday functional limitations. Choice reaction time adds a discrimination component that engages frontal-parietal networks, making it sensitive to both subcortical and cortical pathology.</p></div> `);
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
