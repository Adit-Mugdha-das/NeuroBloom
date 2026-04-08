import { a as attr_class, s as store_get, u as unsubscribe_stores, b as slot } from "../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../chunks/state.svelte.js";
import { p as page } from "../../chunks/stores.js";
import "../../chunks/api.js";
import { l as locale } from "../../chunks/index3.js";
import { u as user, a as authReady } from "../../chunks/stores2.js";
function PublicLanguageSwitcher($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<div class="language-switcher svelte-19cuemb" aria-label="Language switcher" data-localize-skip=""><button type="button"${attr_class("svelte-19cuemb", void 0, {
      "active": store_get($$store_subs ??= {}, "$locale", locale) === "en"
    })}>EN</button> <button type="button"${attr_class("svelte-19cuemb", void 0, {
      "active": store_get($$store_subs ??= {}, "$locale", locale) === "bn"
    })}>বাং</button></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
const PUBLIC_LANGUAGE_ROUTE_PATHS = ["/", "/login", "/register"];
const OBSERVED_DOM_ROUTE_PATHS = [
  "/training",
  "/training/cancellation-test",
  "/training/flanker",
  "/training/inspection-time",
  "/training/multiple-object-tracking",
  "/training/pattern-comparison",
  "/training/stockings-of-cambridge",
  "/training/tower-of-london",
  "/training/trail-making-b",
  "/training/twenty-questions",
  "/training/useful-field-of-view",
  "/training/visual-search",
  "/baseline/tasks/attention",
  "/baseline/tasks/flexibility"
];
const NATIVE_LOCALIZED_ROUTE_PATHS = [
  "/dashboard",
  "/messages",
  "/notifications",
  "/find-doctor",
  "/baseline/tasks/planning",
  "/baseline/tasks/processing-speed",
  "/baseline/tasks/visual-scanning",
  "/baseline/tasks/working-memory",
  "/training/category-fluency",
  "/training/dccs",
  "/training/digit-span",
  "/training/dual-n-back",
  "/training/gonogo",
  "/training/letter-number-sequencing",
  "/training/operation-span",
  "/training/pasat",
  "/training/plus-minus",
  "/training/sdmt",
  "/training/spatial-span",
  "/training/stroop",
  "/training/trail-making-a",
  "/training/verbal-fluency",
  "/training/wcst"
];
const PUBLIC_LANGUAGE_ROUTES = new Set(PUBLIC_LANGUAGE_ROUTE_PATHS);
const OBSERVED_DOM_ROUTES = new Set(OBSERVED_DOM_ROUTE_PATHS);
const NATIVE_LOCALIZED_ROUTES = new Set(NATIVE_LOCALIZED_ROUTE_PATHS);
function getRouteLocalizationMode(pathname = "") {
  if (NATIVE_LOCALIZED_ROUTES.has(pathname)) {
    return "native";
  }
  if (OBSERVED_DOM_ROUTES.has(pathname)) {
    return "observe";
  }
  return "refresh";
}
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let showPublicLanguageSwitcher, localizationMode;
    let currentUser = null;
    user.subscribe((value) => {
      currentUser = value;
    });
    showPublicLanguageSwitcher = store_get($$store_subs ??= {}, "$authReady", authReady) && !currentUser && PUBLIC_LANGUAGE_ROUTES.has(store_get($$store_subs ??= {}, "$page", page).url.pathname);
    localizationMode = getRouteLocalizationMode(store_get($$store_subs ??= {}, "$page", page).url.pathname);
    if (showPublicLanguageSwitcher) {
      $$renderer2.push("<!--[-->");
      PublicLanguageSwitcher($$renderer2);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (localizationMode !== "native") {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="app-localization-root svelte-v5218u"><!--[-->`);
      slot($$renderer2, $$props, "default", {});
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="app-localization-root svelte-v5218u"><!--[-->`);
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
