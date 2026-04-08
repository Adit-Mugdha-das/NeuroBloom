import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import "../../../../chunks/index3.js";
/* empty css                                                               */
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let newBadges = [];
    TASK_PLAY_MODE.RECORDED;
    $$renderer2.push(`<div class="nback-container svelte-184q180" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="page-content svelte-184q180">`);
      LoadingSkeleton($$renderer2, {});
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    if (newBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: newBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
