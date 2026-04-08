import "clsx";
import { o as onDestroy } from "../../../../chunks/index-server.js";
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
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    TASK_PLAY_MODE.RECORDED;
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="sdmt-container svelte-1wyaz9h" data-localize-skip=""><div class="sdmt-inner svelte-1wyaz9h">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-wrapper svelte-1wyaz9h">`);
      LoadingSkeleton($$renderer2, { variant: "card", count: 3 });
      $$renderer2.push(`<!----></div>`);
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
