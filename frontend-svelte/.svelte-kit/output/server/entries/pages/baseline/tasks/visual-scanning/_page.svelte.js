import { Y as head } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalTargets = 5;
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    head("29xk7i", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Visual Scanning Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-29xk7i">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-29xk7i"><h1 class="svelte-29xk7i">Visual Scanning Test</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-29xk7i">Visual Search Task</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-29xk7i"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-29xk7i">Instructions:</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-29xk7i"><li class="svelte-29xk7i">You'll see a grid of letters (L, I, F, E, P, T)</li> <li class="svelte-29xk7i">Find and click ALL the letter <strong style="color: #4caf50; font-size: 24px;" class="svelte-29xk7i">"T"</strong></li> <li class="svelte-29xk7i">There are <strong class="svelte-29xk7i">${escape_html(totalTargets)} targets</strong> hidden in the grid</li> <li class="svelte-29xk7i">Work as quickly and accurately as possible</li> <li class="svelte-29xk7i">Timer starts when the grid appears</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-29xk7i"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-29xk7i">What to Look For:</h4> <div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px;" class="svelte-29xk7i"><div class="svelte-29xk7i"><p style="color: #4caf50; font-size: 48px; font-weight: bold; margin: 0;" class="svelte-29xk7i">T</p> <p style="color: #666; font-size: 14px;" class="svelte-29xk7i">FIND THIS</p></div> <div class="svelte-29xk7i"><p style="color: #999; font-size: 48px; font-weight: bold; margin: 0;" class="svelte-29xk7i">L I F E P</p> <p style="color: #666; font-size: 14px;" class="svelte-29xk7i">IGNORE THESE</p></div></div></div></div> <button class="btn-primary svelte-29xk7i" style="margin-top: 40px;">Start Test</button> <button class="btn-secondary svelte-29xk7i">Back to Dashboard</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
