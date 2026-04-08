import { f as attr_style, b as slot, e as ensure_array_like, a as attr_class, u as unsubscribe_stores, d as bind_props, s as store_get } from "./index2.js";
import { $ as fallback } from "./utils2.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./utils.js";
import { a as attr } from "./attributes.js";
import "@sveltejs/kit/internal/server";
import "./state.svelte.js";
import { p as page } from "./stores.js";
import { t as translateText, l as locale } from "./index3.js";
import { e as escape_html } from "./escaping.js";
function DoctorWorkspaceShell($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let title = fallback($$props["title"], "");
    let subtitle = fallback($$props["subtitle"], "");
    let eyebrow = fallback($$props["eyebrow"], "Doctor Workspace");
    let maxWidth = fallback($$props["maxWidth"], "1260px");
    const navItems = [
      { href: "/doctor/dashboard", label: "Dashboard" },
      { href: "/doctor/patients", label: "Patients" },
      { href: "/doctor/analytics", label: "Analytics" },
      { href: "/doctor/reports", label: "Reports" },
      { href: "/doctor/messages", label: "Messages" },
      { href: "/doctor/notifications", label: "Notifications" }
    ];
    function isActive(href) {
      const currentPath = store_get($$store_subs ??= {}, "$page", page).url.pathname;
      if (href === "/doctor/dashboard") {
        return currentPath === href;
      }
      return currentPath === href || currentPath.startsWith(`${href}/`);
    }
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    $$renderer2.push(`<div class="doctor-shell svelte-b3swc1"><div class="doctor-shell__backdrop svelte-b3swc1"></div> <div class="doctor-shell__inner svelte-b3swc1"${attr_style(`--shell-max-width: ${maxWidth};`)}><header class="doctor-shell__header svelte-b3swc1"><div class="doctor-shell__brand"><p class="doctor-shell__eyebrow svelte-b3swc1">${escape_html(t(eyebrow))}</p> <h1 class="svelte-b3swc1">${escape_html(t(title))}</h1> `);
    if (subtitle) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<p class="doctor-shell__subtitle svelte-b3swc1">${escape_html(t(subtitle))}</p>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="doctor-shell__actions svelte-b3swc1"><!--[-->`);
    slot($$renderer2, $$props, "actions", {});
    $$renderer2.push(`<!--]--> <button class="doctor-shell__logout svelte-b3swc1">${escape_html(t("Logout"))}</button></div></header> <nav class="doctor-shell__nav svelte-b3swc1"${attr("aria-label", t("Doctor Workspace"))}><!--[-->`);
    const each_array = ensure_array_like(navItems);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let item = each_array[$$index];
      $$renderer2.push(`<button${attr_class("doctor-shell__nav-item svelte-b3swc1", void 0, { "active": isActive(item.href) })}>${escape_html(t(item.label))}</button>`);
    }
    $$renderer2.push(`<!--]--></nav> <main class="doctor-shell__content svelte-b3swc1"><!--[-->`);
    slot($$renderer2, $$props, "default", {});
    $$renderer2.push(`<!--]--></main></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { title, subtitle, eyebrow, maxWidth });
  });
}
export {
  DoctorWorkspaceShell as D
};
