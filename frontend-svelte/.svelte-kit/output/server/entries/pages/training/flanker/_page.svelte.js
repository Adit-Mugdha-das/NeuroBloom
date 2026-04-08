import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    TASK_PLAY_MODE.RECORDED;
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="flanker-container svelte-1ksi2bq">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-wrap svelte-1ksi2bq">`);
      LoadingSkeleton($$renderer2, {});
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="help-fab svelte-1ksi2bq" aria-label="Help">?</button>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
