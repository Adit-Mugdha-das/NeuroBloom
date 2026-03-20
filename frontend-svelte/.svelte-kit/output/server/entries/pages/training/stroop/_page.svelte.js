import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
/* empty css                                                                 */
/* empty css                                                               */
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let currentTrialData;
    user.subscribe((value) => {
    });
    currentTrialData = null;
    currentTrialData?.condition === "baseline" ? "Color Patches" : currentTrialData?.condition === "congruent" ? "Matching Words" : "Conflicting Words";
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
  });
}
export {
  _page as default
};
