import "clsx";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import { p as page } from "../../../../../chunks/stores.js";
import "../../../../../chunks/api.js";
import { D as DoctorWorkspaceShell } from "../../../../../chunks/DoctorWorkspaceShell.js";
import { u as user } from "../../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let patientName;
    user.subscribe((value) => {
    });
    page.subscribe((value) => {
      value.params.id;
    });
    patientName = "Patient";
    DoctorWorkspaceShell($$renderer2, {
      title: patientName,
      subtitle: "Patient-specific clinical overview with adherence, focus areas, biomarker access, progress monitoring, and recent activity in one calmer workspace.",
      eyebrow: "Doctor Patient Workspace",
      maxWidth: "1360px",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-rrbi0u"><p>Loading patient workspace...</p></section>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: {
        default: true,
        actions: ($$renderer3) => {
          {
            $$renderer3.push(`<button class="outline-btn svelte-rrbi0u">All Patients</button> <button class="outline-btn svelte-rrbi0u">Progress Reports</button> <button class="outline-btn svelte-rrbi0u">Prescriptions</button> <button class="primary-btn svelte-rrbi0u">Add Clinical Note</button> <button class="accent-btn svelte-rrbi0u">Adjust Training Plan</button>`);
          }
        }
      }
    });
    $$renderer2.push(`<!----> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
