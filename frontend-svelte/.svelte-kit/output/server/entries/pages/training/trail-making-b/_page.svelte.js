import { Y as head } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
/* empty css                                                                 */
/* empty css                                                               */
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    head("1v5sop9", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Trail Making Test - Part B | NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="tmt-b-container svelte-1v5sop9">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-1v5sop9"><div class="spinner svelte-1v5sop9"></div> <p>Loading Trail Making Test - Part B...</p></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
