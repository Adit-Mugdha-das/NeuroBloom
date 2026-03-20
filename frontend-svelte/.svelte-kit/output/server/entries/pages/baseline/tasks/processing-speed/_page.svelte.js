import { Y as head } from "../../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import "../../../../../chunks/api.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let simpleTrials;
    let choiceTrials;
    head("156cj0d", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Processing Speed Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-156cj0d">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-156cj0d"><h1 class="svelte-156cj0d">Processing Speed Test</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-156cj0d">Reaction Time Assessment</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-156cj0d"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-156cj0d">Two-Part Test:</h3> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin: 15px 0;" class="svelte-156cj0d"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-156cj0d">Part 1: Simple Reaction Time</h4> <ul style="line-height: 1.8; color: #666;" class="svelte-156cj0d"><li class="svelte-156cj0d">Screen will turn <strong style="color: #4caf50;" class="svelte-156cj0d">GREEN</strong></li> <li class="svelte-156cj0d">Click as fast as possible when it turns green</li> <li class="svelte-156cj0d">Don't click before it turns green!</li> <li class="svelte-156cj0d">${escape_html(simpleTrials)} trials</li></ul></div> <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 15px 0;" class="svelte-156cj0d"><h4 style="color: #ff9800; margin-bottom: 10px;" class="svelte-156cj0d">Part 2: Choice Reaction Time</h4> <ul style="line-height: 1.8; color: #666;" class="svelte-156cj0d">`);
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<li class="svelte-156cj0d">You'll see <strong class="svelte-156cj0d">Circle ⭕</strong>, <strong class="svelte-156cj0d">Square ⬜</strong>, <strong class="svelte-156cj0d">Triangle 🔺</strong>, or <strong class="svelte-156cj0d">Diamond 🔶</strong></li>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]--> <li class="svelte-156cj0d">Click the matching button as fast as possible</li> <li class="svelte-156cj0d">Fast AND accurate!</li> <li class="svelte-156cj0d">${escape_html(choiceTrials)} trials</li></ul></div></div> <button class="btn-primary svelte-156cj0d" style="margin-top: 40px;">Start Test</button> <button class="btn-secondary svelte-156cj0d">Back to Dashboard</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
