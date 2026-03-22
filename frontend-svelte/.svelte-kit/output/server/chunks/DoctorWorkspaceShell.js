import { d as attr_style, b as slot, e as ensure_array_like, a as attr_class, f as bind_props, s as store_get, u as unsubscribe_stores } from "./index2.js";
import { j as fallback } from "./utils3.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./utils.js";
import { e as escape_html } from "./escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "./state.svelte.js";
import { p as page } from "./stores.js";
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
    $$renderer2.push(`<div class="doctor-shell svelte-14lic82"><div class="doctor-shell__backdrop svelte-14lic82"></div> <div class="doctor-shell__inner svelte-14lic82"${attr_style(`--shell-max-width: ${maxWidth};`)}><header class="doctor-shell__header svelte-14lic82"><div class="doctor-shell__brand"><p class="doctor-shell__eyebrow svelte-14lic82">${escape_html(eyebrow)}</p> <h1 class="svelte-14lic82">${escape_html(title)}</h1> `);
    if (subtitle) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<p class="doctor-shell__subtitle svelte-14lic82">${escape_html(subtitle)}</p>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="doctor-shell__actions svelte-14lic82"><!--[-->`);
    slot($$renderer2, $$props, "actions", {});
    $$renderer2.push(`<!--]--> <button class="doctor-shell__logout svelte-14lic82">Logout</button></div></header> <nav class="doctor-shell__nav svelte-14lic82" aria-label="Doctor workspace"><!--[-->`);
    const each_array = ensure_array_like(navItems);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let item = each_array[$$index];
      $$renderer2.push(`<button${attr_class("doctor-shell__nav-item svelte-14lic82", void 0, { "active": isActive(item.href) })}>${escape_html(item.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></nav> <main class="doctor-shell__content svelte-14lic82"><!--[-->`);
    slot($$renderer2, $$props, "default", {});
    $$renderer2.push(`<!--]--></main></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { title, subtitle, eyebrow, maxWidth });
  });
}
export {
  DoctorWorkspaceShell as D
};
