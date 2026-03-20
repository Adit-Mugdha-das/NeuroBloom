import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import { D as DoctorWorkspaceShell } from "../../../../chunks/DoctorWorkspaceShell.js";
import "../../../../chunks/api.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let notifications = [];
    user.subscribe((value) => {
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Notifications",
      subtitle: "Administrative updates and research notices collected in one quiet workspace so they do not compete with the clinical dashboard.",
      children: ($$renderer3) => {
        $$renderer3.push(`<section class="hero-card svelte-fua1m1"><div><p class="hero-kicker svelte-fua1m1">Practice Updates</p> <h2 class="svelte-fua1m1">${escape_html(notifications.length)} active notices</h2> <p class="svelte-fua1m1">Doctor-facing platform notices, feature updates, and invitations are stored here instead of interrupting patient review.</p></div></section> `);
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-fua1m1"><p class="svelte-fua1m1">Loading notifications...</p></section>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: { default: true }
    });
  });
}
export {
  _page as default
};
