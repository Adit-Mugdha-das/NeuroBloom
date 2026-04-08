import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import "../../../chunks/index3.js";
/* empty css                                                                    */
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="settings-container svelte-17n9dzh"><div class="header svelte-17n9dzh"><button class="back-btn svelte-17n9dzh">← Back to Dashboard</button> <h1 class="svelte-17n9dzh">Settings</h1></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-17n9dzh">Loading settings...</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
