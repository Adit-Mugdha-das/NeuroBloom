import { u as unsubscribe_stores, s as store_get } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { a as localeText, l as locale } from "../../../chunks/index3.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    user.subscribe((value) => {
    });
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    $$renderer2.push(`<div class="page-container svelte-6b6fzq" data-localize-skip=""><h1 class="svelte-6b6fzq">🏥 ${escape_html(lt("Find a Healthcare Provider", "একজন স্বাস্থ্যসেবা প্রদানকারী খুঁজুন"))}</h1> <p class="subtitle svelte-6b6fzq">${escape_html(lt("Browse verified doctors and request assignment for professional monitoring", "যাচাইকৃত চিকিৎসকদের দেখুন এবং পেশাদার পর্যবেক্ষণের জন্য যুক্ত হওয়ার অনুরোধ করুন"))}</p> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-6b6fzq">${escape_html(lt("Loading doctors...", "চিকিৎসকদের তথ্য লোড হচ্ছে..."))}</div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
