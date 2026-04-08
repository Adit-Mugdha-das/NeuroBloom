import { u as unsubscribe_stores, s as store_get } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { t as translateText, l as locale, f as formatNumber } from "../../../chunks/index3.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let notifications = [];
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function totalNoticesLabel(count) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(count)}টি মোট নোটিশ` : `${count} total notices`;
    }
    $$renderer2.push(`<div class="page-shell svelte-13pn0mw" data-localize-skip=""><header class="topbar svelte-13pn0mw"><div><p class="eyebrow svelte-13pn0mw">${escape_html(t("Patient Experience"))}</p> <h1 class="svelte-13pn0mw">${escape_html(t("Notification Center"))}</h1> <p class="subtext svelte-13pn0mw">${escape_html(t("System announcements, feature updates, and research invitations from the NeuroBloom team."))}</p></div> <div class="topbar-actions svelte-13pn0mw"><button class="ghost-btn svelte-13pn0mw">${escape_html(t("Back to Dashboard"))}</button> <button class="logout-btn svelte-13pn0mw">${escape_html(t("Logout"))}</button></div></header> <main class="content svelte-13pn0mw"><section class="hero-card svelte-13pn0mw"><div><p class="hero-kicker svelte-13pn0mw">${escape_html(t("Stay Informed"))}</p> <h2 class="svelte-13pn0mw">${escape_html(t("Your latest platform notices in one place"))}</h2> <p class="svelte-13pn0mw">${escape_html(t("Unread badges on the dashboard clear as soon as you open this page."))}</p></div> <div class="hero-meta"><span class="meta-pill svelte-13pn0mw">${escape_html(totalNoticesLabel(notifications.length))}</span></div></section> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="state-card svelte-13pn0mw">${escape_html(t("Loading notifications..."))}</div>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
