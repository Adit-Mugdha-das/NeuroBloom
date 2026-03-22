import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { l as locale, t as translateText } from "../../../../chunks/index3.js";
/* empty css                                                               */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let earnedBadges = [];
    function taskLocale() {
      return store_get($$store_subs ??= {}, "$locale", locale);
    }
    function t(text, activeLocale = taskLocale()) {
      return translateText(text, activeLocale);
    }
    $$renderer2.push(`<div data-localize-skip="" style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;"><div style="max-width: 900px; margin: 0 auto;">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);"><div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div> <h2 style="color: #667eea;">${escape_html(t("Loading Verbal Fluency Task...", store_get($$store_subs ??= {}, "$locale", locale)))}</h2></div>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    if (earnedBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: earnedBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
