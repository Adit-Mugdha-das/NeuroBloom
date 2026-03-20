import { U as attr_class, V as stringify, W as slot } from "../../chunks/index2.js";
import "../../chunks/api.js";
import { u as user } from "../../chunks/stores.js";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../chunks/state.svelte.js";
function DevPanel($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div${attr_class(`dev-panel ${stringify("")}`, "svelte-laj0xd")}><button class="toggle-btn svelte-laj0xd" title="Dev Tools">🛠️</button> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<!--[-->`);
    slot($$renderer2, $$props, "default", {});
    $$renderer2.push(`<!--]--> `);
    DevPanel($$renderer2);
    $$renderer2.push(`<!---->`);
  });
}
export {
  _layout as default
};
