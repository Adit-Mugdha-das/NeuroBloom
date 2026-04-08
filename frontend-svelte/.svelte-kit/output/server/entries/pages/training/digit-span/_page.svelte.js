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
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="digit-span-container svelte-1tryewj" data-localize-skip=""><div class="digit-span-inner svelte-1tryewj">`);
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
