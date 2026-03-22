import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { t as translateText, l as locale } from "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let currentTrialData;
    user.subscribe((value) => {
    });
    currentTrialData = null;
    currentTrialData?.condition === "baseline" ? translateText("Color Patches", store_get($$store_subs ??= {}, "$locale", locale)) : currentTrialData?.condition === "congruent" ? translateText("Matching Words", store_get($$store_subs ??= {}, "$locale", locale)) : translateText("Conflicting Words", store_get($$store_subs ??= {}, "$locale", locale));
    $$renderer2.push(`<div class="stroop-container svelte-1dur7r">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-1dur7r"><div class="spinner svelte-1dur7r"></div> <p class="svelte-1dur7r">Loading task...</p></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="help-button svelte-1dur7r" aria-label="Help">?</button>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
