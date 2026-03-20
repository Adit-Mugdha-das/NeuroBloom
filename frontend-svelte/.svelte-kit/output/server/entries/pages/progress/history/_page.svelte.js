import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="progress-panel">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="state-panel glass-card svelte-hn5kk5"><p class="svelte-hn5kk5">Loading training history...</p></section>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
