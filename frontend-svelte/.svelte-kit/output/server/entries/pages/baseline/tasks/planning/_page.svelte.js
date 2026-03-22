import { h as head } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let optimalMoves = 7;
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    head("1ksrvw9", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Planning Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-1ksrvw9">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-1ksrvw9"><h1 class="svelte-1ksrvw9">Planning Test</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-1ksrvw9">Tower of Hanoi</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-1ksrvw9"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-1ksrvw9">Instructions:</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-1ksrvw9"><li class="svelte-1ksrvw9">Move all disks from the first tower to the third tower</li> <li class="svelte-1ksrvw9">You can only move one disk at a time</li> <li class="svelte-1ksrvw9">A larger disk cannot be placed on a smaller disk</li> <li class="svelte-1ksrvw9">Try to complete in <strong class="svelte-1ksrvw9">minimum moves (${escape_html(optimalMoves)})</strong></li> <li class="svelte-1ksrvw9">Think before you move - planning is key!</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-1ksrvw9"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-1ksrvw9">How to Play:</h4> <p style="color: #666; line-height: 1.6;" class="svelte-1ksrvw9">1. Click on a tower to pick up the top disk<br class="svelte-1ksrvw9"/> 2. Click on another tower to place it<br class="svelte-1ksrvw9"/> 3. Goal: Get all disks on the rightmost tower</p></div></div> <button class="btn-primary svelte-1ksrvw9" style="margin-top: 40px;">Start Test</button> <button class="btn-secondary svelte-1ksrvw9">Back to Dashboard</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
