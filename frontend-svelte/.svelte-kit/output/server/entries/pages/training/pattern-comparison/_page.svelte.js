import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/index3.js";
/* empty css                                                               */
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
/* empty css                                                                 */
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    TASK_PLAY_MODE.RECORDED;
    $$renderer2.push(`<div class="pc-container svelte-1f0cm4n" data-localize-skip=""><div class="pc-inner svelte-1f0cm4n">`);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, { variant: "card", count: 3 });
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
