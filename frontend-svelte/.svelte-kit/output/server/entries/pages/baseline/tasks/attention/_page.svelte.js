import { h as head } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalTrials = 60;
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    head("thcug0", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Attention Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-thcug0">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-thcug0"><h1 class="svelte-thcug0">Attention Test</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-thcug0">Continuous Performance Test (CPT)</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-thcug0"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-thcug0">Instructions:</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-thcug0"><li class="svelte-thcug0">Letters will appear rapidly on screen (1 per second)</li> <li class="svelte-thcug0"><strong class="svelte-thcug0">Click ONLY</strong> when you see <strong class="svelte-thcug0">X after A</strong> (the AX sequence)</li> <li class="svelte-thcug0">Do NOT click for any other letter or combination</li> <li class="svelte-thcug0">Stay focused for the entire duration</li> <li class="svelte-thcug0">Total duration: ~1 minute (${escape_html(totalTrials)} trials)</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-thcug0"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-thcug0">Example:</h4> <p style="color: #666;" class="svelte-thcug0">Sequence: B → A → <strong style="color: #4caf50;" class="svelte-thcug0">X</strong> ← CLICK HERE</p> <p style="color: #666;" class="svelte-thcug0">Sequence: A → B → X ← DON'T CLICK (not AX)</p> <p style="color: #666;" class="svelte-thcug0">Sequence: A → <strong style="color: #f44336;" class="svelte-thcug0">K</strong> ← DON'T CLICK</p></div></div> <button class="btn-primary svelte-thcug0" style="margin-top: 40px;">Start Test</button> <button class="btn-secondary svelte-thcug0">Back to Dashboard</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
