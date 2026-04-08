import { h as head, s as store_get, u as unsubscribe_stores } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import "../../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../../chunks/TaskPracticeActions.js";
import { a as localeText, l as locale } from "../../../../../chunks/index3.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let totalTrials = 40;
    let practiceStatusMessage = "";
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    head("mfgons", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Cognitive Flexibility Test - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-mfgons">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-mfgons"><h1 class="svelte-mfgons">Cognitive Flexibility Test</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-mfgons">Task Switching</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-mfgons"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-mfgons">Instructions:</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-mfgons"><li class="svelte-mfgons">You will see numbers with colored backgrounds</li> <li class="svelte-mfgons"><strong style="color: #2196f3;" class="svelte-mfgons">BLUE background:</strong> Judge if the number is odd or even</li> <li class="svelte-mfgons"><strong style="color: #f44336;" class="svelte-mfgons">RED background:</strong> Judge if the number is >5 or &lt;5</li> <li class="svelte-mfgons">The background color changes randomly - stay flexible!</li> <li class="svelte-mfgons">Total trials: ${escape_html(totalTrials)}</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-mfgons"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-mfgons">Examples:</h4> <div style="background: #2196f3; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;" class="svelte-mfgons"><strong class="svelte-mfgons">7</strong> on BLUE → "Odd" (because 7 is odd)</div> <div style="background: #f44336; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;" class="svelte-mfgons"><strong class="svelte-mfgons">7</strong> on RED → "High" (because 7 > 5)</div> <div style="background: #2196f3; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;" class="svelte-mfgons"><strong class="svelte-mfgons">2</strong> on BLUE → "Even" (because 2 is even)</div></div></div> `);
      TaskPracticeActions($$renderer2, {
        locale: store_get($$store_subs ??= {}, "$locale", locale),
        startLabel: localeText({ en: "Start Actual Task", bn: "আসল টাস্ক শুরু করুন" }, store_get($$store_subs ??= {}, "$locale", locale)),
        statusMessage: practiceStatusMessage,
        align: "center"
      });
      $$renderer2.push(`<!----> <button class="btn-secondary svelte-mfgons">Back to Dashboard</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
