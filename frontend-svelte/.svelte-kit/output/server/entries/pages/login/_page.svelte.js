import { s as store_get, a as attr_class, u as unsubscribe_stores, c as stringify } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { a as attr } from "../../../chunks/attributes.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { t as translateText, l as locale } from "../../../chunks/index3.js";
import { e as escape_html } from "../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let loginButtonLabel;
    let email = "";
    let password = "";
    let loginType = "patient";
    let loading = false;
    function getLoginButtonLabel(type, activeLocale) {
      return translateText("Login as Patient", activeLocale);
    }
    loginButtonLabel = getLoginButtonLabel(loginType, store_get($$store_subs ??= {}, "$locale", locale));
    $$renderer2.push(`<div class="auth-container"><div class="auth-card"><h1>Welcome Back</h1> <p>Login to continue your cognitive training</p> <div class="login-type-selector svelte-1x05zx6"><button type="button"${attr_class(`type-btn ${stringify("active")}`, "svelte-1x05zx6")}${attr("disabled", loading, true)}>👤 ${escape_html(translateText("Patient", store_get($$store_subs ??= {}, "$locale", locale)))}</button> <button type="button"${attr_class(`type-btn ${stringify("")}`, "svelte-1x05zx6")}${attr("disabled", loading, true)}>👨‍⚕️ ${escape_html(translateText("Doctor", store_get($$store_subs ??= {}, "$locale", locale)))}</button> <button type="button"${attr_class(`type-btn ${stringify("")}`, "svelte-1x05zx6")}${attr("disabled", loading, true)}>🏥 ${escape_html(translateText("Admin", store_get($$store_subs ??= {}, "$locale", locale)))}</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <form><div class="form-group"><label for="email">Email</label> <input type="email" id="email"${attr("value", email)} placeholder="your@email.com"${attr("disabled", loading, true)}/></div> <div class="form-group"><label for="password">Password</label> <input type="password" id="password"${attr("value", password)} placeholder="••••••••"${attr("disabled", loading, true)}/></div> <button type="submit" class="btn"${attr("disabled", loading, true)}>${escape_html(loginButtonLabel)}</button></form> <div class="auth-link">${escape_html(translateText("Don't have an account?", store_get($$store_subs ??= {}, "$locale", locale)))} <a href="/register">${escape_html(translateText("Register here", store_get($$store_subs ??= {}, "$locale", locale)))}</a></div></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
