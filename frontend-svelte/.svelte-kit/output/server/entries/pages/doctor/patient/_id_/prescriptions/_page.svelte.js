import "clsx";
import "@sveltejs/kit/internal";
import "../../../../../../chunks/exports.js";
import "../../../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../../../chunks/state.svelte.js";
import { p as page } from "../../../../../../chunks/stores.js";
import "../../../../../../chunks/api.js";
import { D as DoctorWorkspaceShell } from "../../../../../../chunks/DoctorWorkspaceShell.js";
import { u as user } from "../../../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let patientName, latestActivePrescription;
    let prescriptions = [];
    let summary = { total: 0, active: 0 };
    user.subscribe((value) => {
    });
    page.subscribe((value) => {
      value.params.id;
    });
    function createMedication() {
      return {
        name: "",
        dosage: "",
        frequency: "",
        duration: "",
        instructions: ""
      };
    }
    function createDraft() {
      return {
        title: "",
        summary: "",
        patient_instructions: "",
        clinician_notes: "",
        follow_up_plan: "",
        status: "active",
        valid_until: "",
        review_date: "",
        lifestyle_plan_text: "",
        medications: [createMedication()]
      };
    }
    let draft = createDraft();
    function formatDate(dateValue) {
      if (!dateValue) return "Not scheduled";
      return new Date(dateValue).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
    }
    draft.medications.map((item) => ({
      ...item,
      name: item.name.trim(),
      dosage: item.dosage.trim(),
      frequency: item.frequency.trim()
    })).filter((item) => item.name || item.dosage || item.frequency || item.duration || item.instructions);
    draft.lifestyle_plan_text.split("\n").map((item) => item.trim()).filter(Boolean);
    patientName = "Patient";
    latestActivePrescription = prescriptions.find((prescription) => prescription.status === "active") || null;
    [
      { label: "Total Prescriptions", value: summary.total },
      { label: "Active", value: summary.active },
      {
        label: "Latest Review",
        value: latestActivePrescription?.review_date ? formatDate(latestActivePrescription.review_date) : "Not scheduled"
      },
      {
        label: "Diagnosis",
        value: "Not recorded"
      }
    ];
    DoctorWorkspaceShell($$renderer2, {
      title: `Prescriptions · ${patientName}`,
      subtitle: "Structured digital prescribing with revision history, clinician review, PDF generation, and patient delivery.",
      eyebrow: "Doctor Patient Workspace",
      maxWidth: "1360px",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-1x41m0j"><p class="svelte-1x41m0j">Loading prescriptions...</p></section>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: {
        default: true,
        actions: ($$renderer3) => {
          {
            $$renderer3.push(`<button class="outline-btn svelte-1x41m0j">Patient Overview</button> <button class="outline-btn svelte-1x41m0j">Reports</button> <button class="primary-btn svelte-1x41m0j">Create Prescription</button>`);
          }
        }
      }
    });
    $$renderer2.push(`<!----> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
