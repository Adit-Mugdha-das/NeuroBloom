import { u as unsubscribe_stores, s as store_get } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { t as translateText, l as locale } from "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 2rem;" data-localize-skip="" class="svelte-vbp3bn"><div style="max-width: 900px; margin: 0 auto;" class="svelte-vbp3bn">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);" class="svelte-vbp3bn"><div style="font-size: 3rem; margin-bottom: 1rem;" class="svelte-vbp3bn">⏳</div> <h2 style="color: #8b5cf6;" class="svelte-vbp3bn">${escape_html(t("Loading Category Fluency Task..."))}</h2></div>`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
