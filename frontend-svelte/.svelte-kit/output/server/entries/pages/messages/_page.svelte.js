import { u as unsubscribe_stores, s as store_get } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { t as translateText, l as locale } from "../../../chunks/index3.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    $$renderer2.push(`<div class="messages-page svelte-1v8ama" data-localize-skip=""><div class="chat-container svelte-1v8ama">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-1v8ama"><div class="spinner svelte-1v8ama"></div> <p class="svelte-1v8ama">${escape_html(t("Loading messages..."))}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
