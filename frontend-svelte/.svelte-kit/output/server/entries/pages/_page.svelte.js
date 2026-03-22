import { s as store_get, u as unsubscribe_stores } from "../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/utils.js";
import { e as escape_html } from "../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../chunks/state.svelte.js";
import { t as translateText, l as locale } from "../../chunks/index3.js";
import { u as user } from "../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let welcomeMessage;
    let currentUser = null;
    user.subscribe((value) => {
      currentUser = value;
    });
    welcomeMessage = currentUser ? translateText(`Welcome back, ${currentUser.email}!`, store_get($$store_subs ??= {}, "$locale", locale)) : "";
    $$renderer2.push(`<div class="auth-container"><div class="auth-card"><h1>🧠 NeuroBloom</h1> <p>Clinical-Grade Cognitive Assessment Platform</p> `);
    if (currentUser) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div style="margin-top: 30px;"><p style="color: #667eea; font-weight: 600; margin-bottom: 20px;">${escape_html(welcomeMessage)}</p> <button class="btn">Continue to Dashboard</button> <a href="/login?reset=1"><button class="btn-secondary" style="width: 100%; margin-top: 10px;">Switch Account</button></a></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div style="margin-top: 30px;"><a href="/login"><button class="btn" style="margin-bottom: 15px;">Login</button></a> <a href="/register"><button class="btn-secondary" style="width: 100%;">Create Account</button></a></div>`);
    }
    $$renderer2.push(`<!--]--> <div style="margin-top: 40px; text-align: center; color: #666; font-size: 14px;"><p>Personalized cognitive training with adaptive AI</p> <p style="margin-top: 10px;">MS-specific features • Weekly progress tracking</p></div></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
