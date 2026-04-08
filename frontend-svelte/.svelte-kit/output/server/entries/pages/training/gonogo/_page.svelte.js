import { h as head, u as unsubscribe_stores, s as store_get } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { l as locale, a as localeText } from "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { g as getGoNoGoStimulusPair } from "../../../../chunks/task-ui.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let displayStimuli;
    let sessionData = null;
    TASK_PLAY_MODE.RECORDED;
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
    head("imliq4", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(lt("Go/No-Go Task - NeuroBloom", "গো/নো-গো টাস্ক - NeuroBloom"))}</title>`);
      });
    });
    $$renderer2.push(`<div class="gonogo-container svelte-imliq4" data-localize-skip=""><div class="gonogo-inner svelte-imliq4">`);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, { variant: "card", count: 3 });
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
