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
    let mergedPatients;
    let searchTerm = "";
    let riskFilter = "all";
    let sortBy = "name";
    user.subscribe((value) => {
    });
    mergedPatients = [];
    mergedPatients.filter((patient) => {
      const query = searchTerm.trim().toLowerCase();
      const matchesSearch = !query || [patient.name, patient.email, patient.diagnosis].filter(Boolean).some((value) => value.toLowerCase().includes(query));
      const matchesRisk = riskFilter === "all";
      return matchesSearch && matchesRisk;
    }).sort((left, right) => {
      let leftValue = left[sortBy];
      let rightValue = right[sortBy];
      {
        leftValue = (left.name || "").toLowerCase();
        rightValue = (right.name || "").toLowerCase();
      }
      if (leftValue < rightValue) return -1;
      if (leftValue > rightValue) return 1;
      return 0;
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Patients",
      subtitle: "A dedicated patient management view for searching, filtering, and opening detailed records without crowding the dashboard.",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-114lblx"><p class="svelte-114lblx">Loading patient list...</p></section>`);
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
