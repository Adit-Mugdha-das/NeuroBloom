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
    let confirmPassword = "";
    let fullName = "";
    let loading = false;
    $$renderer2.push(`<div class="auth-container"><div class="auth-card"><h1>Create Account</h1> <p>Start your cognitive training journey</p> <div class="register-type-selector svelte-52fghe"><button type="button"${attr_class(`type-btn ${stringify("active")}`, "svelte-52fghe")}${attr("disabled", loading, true)}>👤 Patient</button> <button type="button"${attr_class(`type-btn ${stringify("")}`, "svelte-52fghe")}${attr("disabled", loading, true)}>👨‍⚕️ Doctor</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <form><div class="form-group"><label for="fullName">Full Name *</label> <input type="text" id="fullName"${attr("value", fullName)}${attr("placeholder", "Jane Smith")}${attr("disabled", loading, true)} required/></div> <div class="form-group"><label for="email">Email</label> <input type="email" id="email"${attr("value", email)} placeholder="your@email.com"${attr("disabled", loading, true)} required/></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="form-group"><label for="password">Password</label> <input type="password" id="password"${attr("value", password)} placeholder="••••••••"${attr("disabled", loading, true)} required/></div> <div class="form-group"><label for="confirmPassword">Confirm Password</label> <input type="password" id="confirmPassword"${attr("value", confirmPassword)} placeholder="••••••••"${attr("disabled", loading, true)} required/></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <button type="submit" class="btn"${attr("disabled", false, true)}>`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Register as ${escape_html("Patient")}`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></button></form> <div class="auth-link">Already have an account? <a href="/login">Login here</a></div></div></div>`);
  });
}
export {
  _page as default
};
