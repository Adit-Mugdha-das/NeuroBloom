import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DoctorWorkspaceShell } from "../../../../chunks/DoctorWorkspaceShell.js";
import "../../../../chunks/api.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Dashboard",
      subtitle: "A compact clinician overview focused on attention, pending actions, and a quick cohort readout.",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[!-->");
        }
        $$renderer3.push(`<!--]--> `);
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-1ifr81p"><p>Loading doctor dashboard...</p></section>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: {
        default: true,
        actions: ($$renderer3) => {
          {
            $$renderer3.push(`<button class="header-action svelte-1ifr81p">Messages</button> <button class="header-action notification svelte-1ifr81p">Notifications `);
            {
              $$renderer3.push("<!--[!-->");
            }
            $$renderer3.push(`<!--]--></button>`);
          }
        }
      }
    });
  });
}
export {
  _page as default
};
