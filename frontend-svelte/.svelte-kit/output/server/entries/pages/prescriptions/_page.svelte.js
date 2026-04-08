import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="page-shell svelte-1gi0k59"><header class="topbar svelte-1gi0k59"><div><p class="eyebrow svelte-1gi0k59">NeuroBloom</p> <h1 class="svelte-1gi0k59">My Prescriptions</h1> <p class="subcopy svelte-1gi0k59">Digital prescriptions issued by your clinician, available to review online or download as a PDF.</p></div> <div class="header-actions svelte-1gi0k59"><button class="ghost-btn svelte-1gi0k59">Back To Dashboard</button> <button class="ghost-btn svelte-1gi0k59">Messages</button></div></header> <main class="page-main svelte-1gi0k59">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="state-card svelte-1gi0k59"><p class="svelte-1gi0k59">Loading prescriptions...</p></section>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
  });
}
export {
  _page as default
};
