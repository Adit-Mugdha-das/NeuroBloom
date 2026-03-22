import { h as head } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalTrials = 40;
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    head("4etfcv", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Cognitive Flexibility Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-4etfcv">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-4etfcv"><h1 class="svelte-4etfcv">Cognitive Flexibility Test</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-4etfcv">Task Switching</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-4etfcv"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-4etfcv">Instructions:</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-4etfcv"><li class="svelte-4etfcv">You will see numbers with colored backgrounds</li> <li class="svelte-4etfcv"><strong style="color: #2196f3;" class="svelte-4etfcv">BLUE background:</strong> Judge if the number is odd or even</li> <li class="svelte-4etfcv"><strong style="color: #f44336;" class="svelte-4etfcv">RED background:</strong> Judge if the number is >5 or &lt;5</li> <li class="svelte-4etfcv">The background color changes randomly - stay flexible!</li> <li class="svelte-4etfcv">Total trials: ${escape_html(totalTrials)}</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-4etfcv"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-4etfcv">Examples:</h4> <div style="background: #2196f3; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;" class="svelte-4etfcv"><strong class="svelte-4etfcv">7</strong> on BLUE → "Odd" (because 7 is odd)</div> <div style="background: #f44336; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;" class="svelte-4etfcv"><strong class="svelte-4etfcv">7</strong> on RED → "High" (because 7 > 5)</div> <div style="background: #2196f3; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;" class="svelte-4etfcv"><strong class="svelte-4etfcv">2</strong> on BLUE → "Even" (because 2 is even)</div></div></div> <button class="btn-primary svelte-4etfcv" style="margin-top: 40px;">Start Test</button> <button class="btn-secondary svelte-4etfcv">Back to Dashboard</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
