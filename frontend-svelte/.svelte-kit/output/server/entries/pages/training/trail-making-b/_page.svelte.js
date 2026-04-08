import { h as head, u as unsubscribe_stores, s as store_get } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { t as translateText, l as locale } from "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    TASK_PLAY_MODE.RECORDED;
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    user.subscribe((value) => {
    });
    head("1mxchmi", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(t("Trail Making Test - Part B"))} | NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="tmtb-container svelte-1mxchmi">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-wrap svelte-1mxchmi">`);
      LoadingSkeleton($$renderer2, {});
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="help-fab svelte-1mxchmi" aria-label="Help">?</button>`);
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
