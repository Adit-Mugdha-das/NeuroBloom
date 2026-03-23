import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { L as LoadingSkeleton } from "../../../../chunks/LoadingSkeleton.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="dual-n-back-page svelte-11qvr0n" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      LoadingSkeleton($$renderer2, { variant: "card", count: 3 });
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
