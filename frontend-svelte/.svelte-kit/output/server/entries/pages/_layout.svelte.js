import { a as attr_class, s as store_get, u as unsubscribe_stores, b as slot } from "../../chunks/index2.js";
import { p as page } from "../../chunks/stores.js";
import "../../chunks/api.js";
import { l as locale } from "../../chunks/index3.js";
import { u as user, a as authReady } from "../../chunks/stores2.js";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../chunks/state.svelte.js";
function PublicLanguageSwitcher($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<div class="language-switcher svelte-1cpth08" aria-label="Language switcher" data-localize-skip=""><button type="button"${attr_class("svelte-1cpth08", void 0, {
      "active": store_get($$store_subs ??= {}, "$locale", locale) === "en"
    })}>EN</button> <button type="button"${attr_class("svelte-1cpth08", void 0, {
      "active": store_get($$store_subs ??= {}, "$locale", locale) === "bn"
    })}>বাং</button></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let showPublicLanguageSwitcher, useLegacyDomLocalization;
    let currentUser = null;
    const PUBLIC_LANGUAGE_ROUTES = /* @__PURE__ */ new Set(["/", "/login", "/register"]);
    const NATIVE_LOCALIZED_ROUTES = /* @__PURE__ */ new Set([
      "/baseline/tasks/working-memory",
      "/training/category-fluency",
      "/training/flanker",
      "/training/gonogo",
      "/training/operation-span",
      "/training/pasat",
      "/training/verbal-fluency"
    ]);
    user.subscribe((value) => {
      currentUser = value;
    });
    showPublicLanguageSwitcher = store_get($$store_subs ??= {}, "$authReady", authReady) && !currentUser && PUBLIC_LANGUAGE_ROUTES.has(store_get($$store_subs ??= {}, "$page", page).url.pathname);
    useLegacyDomLocalization = !NATIVE_LOCALIZED_ROUTES.has(store_get($$store_subs ??= {}, "$page", page).url.pathname);
    if (showPublicLanguageSwitcher) {
      $$renderer2.push("<!--[-->");
      PublicLanguageSwitcher($$renderer2);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (useLegacyDomLocalization) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="app-localization-root svelte-12qhfyh"><!--[-->`);
      slot($$renderer2, $$props, "default", {});
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="app-localization-root svelte-12qhfyh"><!--[-->`);
      slot($$renderer2, $$props, "default", {});
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _layout as default
};
