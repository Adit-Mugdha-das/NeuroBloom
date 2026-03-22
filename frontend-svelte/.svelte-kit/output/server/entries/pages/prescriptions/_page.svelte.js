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
    $$renderer2.push(`<div class="page-shell svelte-12tv212"><header class="topbar svelte-12tv212"><div><p class="eyebrow svelte-12tv212">NeuroBloom</p> <h1 class="svelte-12tv212">My Prescriptions</h1> <p class="subcopy svelte-12tv212">Digital prescriptions issued by your clinician, available to review online or download as a PDF.</p></div> <div class="header-actions svelte-12tv212"><button class="ghost-btn svelte-12tv212">Back To Dashboard</button> <button class="ghost-btn svelte-12tv212">Messages</button></div></header> <main class="page-main svelte-12tv212">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="state-card svelte-12tv212"><p class="svelte-12tv212">Loading prescriptions...</p></section>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
  });
}
export {
  _page as default
};
