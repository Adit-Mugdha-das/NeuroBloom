import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { h as domainOrder } from "../../../../chunks/progress.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let metrics = null;
    user.subscribe((value) => {
    });
    domainOrder.map((domain) => ({ domain, data: metrics?.metrics_by_domain?.[domain] })).filter((entry) => entry.data);
    $$renderer2.push(`<div class="progress-panel">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="state-panel glass-card svelte-1w07wmi"><p class="svelte-1w07wmi">Loading domain performance...</p></section>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
