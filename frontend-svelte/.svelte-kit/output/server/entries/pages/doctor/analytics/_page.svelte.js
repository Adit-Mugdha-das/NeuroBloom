import "clsx";
import { D as DoctorWorkspaceShell } from "../../../../chunks/DoctorWorkspaceShell.js";
import "../../../../chunks/api.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Analytics",
      subtitle: "Clinician analytics organized by timeframe so current monitoring, lifetime summary, and longitudinal signals are clearly separated.",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-1elgekq"><p class="svelte-1elgekq">Loading analytics...</p></section>`);
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
