import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
/* empty css                                                       */
import { L as LoadingSkeleton } from "../../../chunks/LoadingSkeleton.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="summary-container svelte-cej6g9">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-container svelte-cej6g9">`);
      LoadingSkeleton($$renderer2, { variant: "card", count: 4 });
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
