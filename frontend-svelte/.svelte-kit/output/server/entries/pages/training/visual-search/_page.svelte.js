import "clsx";
import { o as onDestroy } from "../../../../chunks/index-server.js";
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
    let earnedBadges = [];
    TASK_PLAY_MODE.RECORDED;
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="vs-page svelte-hcv70o" data-localize-skip=""><div class="vs-wrapper svelte-hcv70o">`);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, {});
    }
    $$renderer2.push(`<!--]--></div></div> `);
    if (earnedBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: earnedBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
