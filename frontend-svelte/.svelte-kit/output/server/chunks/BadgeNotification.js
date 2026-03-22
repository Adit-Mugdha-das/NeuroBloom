import { s as store_get, u as unsubscribe_stores, f as bind_props } from "./index2.js";
import { j as fallback } from "./utils3.js";
import { t as translateText, f as formatNumber, l as locale } from "./index3.js";
/* empty css                                                */
function BadgeNotification($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let currentBadge;
    let badges = fallback($$props["badges"], () => [], true);
    let currentBadgeIndex = 0;
    currentBadge = badges[currentBadgeIndex];
    currentBadge ? translateText(currentBadge.name, store_get($$store_subs ??= {}, "$locale", locale)) : "";
    currentBadge ? translateText(currentBadge.description, store_get($$store_subs ??= {}, "$locale", locale)) : "";
    badges.length > 1 ? `${formatNumber(currentBadgeIndex + 1, store_get($$store_subs ??= {}, "$locale", locale))} ${translateText("of", store_get($$store_subs ??= {}, "$locale", locale))} ${formatNumber(badges.length, store_get($$store_subs ??= {}, "$locale", locale))} ${translateText("new badges", store_get($$store_subs ??= {}, "$locale", locale))}` : "";
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { badges });
  });
}
export {
  BadgeNotification as B
};
