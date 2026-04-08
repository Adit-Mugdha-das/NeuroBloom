import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { D as DoctorWorkspaceShell } from "../../../../chunks/DoctorWorkspaceShell.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Prescriptions",
      subtitle: "Issue, track, and revise structured digital prescriptions with PDF output and patient delivery from one clinical workspace.",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-11nyx3p"><p class="svelte-11nyx3p">Loading prescription directory...</p></section>`);
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
