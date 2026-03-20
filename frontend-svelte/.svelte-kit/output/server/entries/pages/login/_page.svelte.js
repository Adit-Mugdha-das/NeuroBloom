import { U as attr_class, V as stringify } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { a as attr } from "../../../chunks/attributes.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { e as escape_html } from "../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let email = "";
    let password = "";
    let loading = false;
    $$renderer2.push(`<div class="auth-container"><div class="auth-card"><h1>Welcome Back</h1> <p>Login to continue your cognitive training</p> <div class="login-type-selector svelte-1x05zx6"><button type="button"${attr_class(`type-btn ${stringify("active")}`, "svelte-1x05zx6")}${attr("disabled", loading, true)}>👤 Patient</button> <button type="button"${attr_class(`type-btn ${stringify("")}`, "svelte-1x05zx6")}${attr("disabled", loading, true)}>👨‍⚕️ Doctor</button> <button type="button"${attr_class(`type-btn ${stringify("")}`, "svelte-1x05zx6")}${attr("disabled", loading, true)}>🏥 Admin</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <form><div class="form-group"><label for="email">Email</label> <input type="email" id="email"${attr("value", email)} placeholder="your@email.com"${attr("disabled", loading, true)}/></div> <div class="form-group"><label for="password">Password</label> <input type="password" id="password"${attr("value", password)} placeholder="••••••••"${attr("disabled", loading, true)}/></div> <button type="submit" class="btn"${attr("disabled", loading, true)}>${escape_html(`Login as ${"Patient"}`)}</button></form> <div class="auth-link">Don't have an account? <a href="/register">Register here</a></div></div></div>`);
  });
}
export {
  _page as default
};
