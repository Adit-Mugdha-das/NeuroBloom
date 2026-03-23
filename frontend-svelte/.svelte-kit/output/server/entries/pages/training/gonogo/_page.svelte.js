import { u as unsubscribe_stores, s as store_get } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { a as attr } from "../../../../chunks/attributes.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { a as localeText, l as locale } from "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { g as getGoNoGoStimulusPair } from "../../../../chunks/task-ui.js";
import { u as user } from "../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let displayStimuli;
    let sessionData = null;
    user.subscribe((value) => {
    });
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function getDisplayStimulusPair() {
      return getGoNoGoStimulusPair(sessionData?.stimulus_set, store_get($$store_subs ??= {}, "$locale", locale), {
        go: "",
        nogo: ""
      });
    }
    displayStimuli = getDisplayStimulusPair();
    displayStimuli.go;
    displayStimuli.nogo;
    $$renderer2.push(`<div class="gonogo-container svelte-1k0owln" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-1k0owln"><div class="spinner svelte-1k0owln"></div> <p class="svelte-1k0owln">${escape_html(lt("Loading task...", "টাস্ক লোড হচ্ছে..."))}</p></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="help-button svelte-1k0owln"${attr("aria-label", lt("Help", "সহায়তা"))}>?</button>`);
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
