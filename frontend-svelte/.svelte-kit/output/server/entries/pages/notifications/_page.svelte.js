import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let notifications = [];
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="page-shell svelte-1ce0uvz"><header class="topbar svelte-1ce0uvz"><div><p class="eyebrow svelte-1ce0uvz">Patient Experience</p> <h1 class="svelte-1ce0uvz">Notification Center</h1> <p class="subtext svelte-1ce0uvz">System announcements, feature updates, and research invitations from the NeuroBloom team.</p></div> <div class="topbar-actions svelte-1ce0uvz"><button class="ghost-btn svelte-1ce0uvz">Back to Dashboard</button> <button class="logout-btn svelte-1ce0uvz">Logout</button></div></header> <main class="content svelte-1ce0uvz"><section class="hero-card svelte-1ce0uvz"><div><p class="hero-kicker svelte-1ce0uvz">Stay Informed</p> <h2 class="svelte-1ce0uvz">Your latest platform notices in one place</h2> <p class="svelte-1ce0uvz">Unread badges on the dashboard clear as soon as you open this page.</p></div> <div class="hero-meta"><span class="meta-pill svelte-1ce0uvz">${escape_html(notifications.length)} total notices</span></div></section> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="state-card svelte-1ce0uvz">Loading notifications...</div>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
  });
}
export {
  _page as default
};
