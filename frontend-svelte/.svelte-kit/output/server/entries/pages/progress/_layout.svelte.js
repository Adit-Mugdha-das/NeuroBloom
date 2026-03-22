import { e as ensure_array_like, a as attr_class, b as slot } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { a as attr } from "../../../chunks/attributes.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import { p as page } from "../../../chunks/index4.js";
import { u as user } from "../../../chunks/stores2.js";
import { e as escape_html } from "../../../chunks/escaping.js";
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let currentUser = null;
    user.subscribe((value) => {
      currentUser = value;
    });
    const tabs = [
      { href: "/progress", label: "Overview" },
      { href: "/progress/domains", label: "Domain Performance" },
      { href: "/progress/history", label: "Training History" },
      { href: "/progress/achievements", label: "Achievements" }
    ];
    function isActive(href) {
      return href === "/progress" ? page.url.pathname === href : page.url.pathname.startsWith(href);
    }
    $$renderer2.push(`<div class="progress-shell svelte-rtgd5r"><header class="progress-header svelte-rtgd5r"><div class="header-copy svelte-rtgd5r"><p class="eyebrow svelte-rtgd5r">NeuroBloom Progress</p> <h1 class="svelte-rtgd5r">Your Progress Area</h1> <p class="header-subcopy svelte-rtgd5r">Each view focuses on one purpose only, so reviewing progress stays calm and easy to follow.</p></div> <div class="header-actions svelte-rtgd5r">`);
    if (currentUser) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="user-email svelte-rtgd5r">${escape_html(currentUser.email)}</span>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <button class="back-btn svelte-rtgd5r">Back to Dashboard</button></div></header> <nav class="progress-nav svelte-rtgd5r" aria-label="Progress sections"><!--[-->`);
    const each_array = ensure_array_like(tabs);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      $$renderer2.push(`<a${attr("href", tab.href)}${attr_class("svelte-rtgd5r", void 0, { "selected": isActive(tab.href) })}>${escape_html(tab.label)}</a>`);
    }
    $$renderer2.push(`<!--]--></nav> <div class="progress-content svelte-rtgd5r"><!--[-->`);
    slot($$renderer2, $$props, "default", {});
    $$renderer2.push(`<!--]--></div></div>`);
  });
}
export {
  _layout as default
};
