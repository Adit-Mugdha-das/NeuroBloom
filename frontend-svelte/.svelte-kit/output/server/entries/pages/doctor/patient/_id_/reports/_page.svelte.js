import { a as attr } from "../../../../../../chunks/attributes.js";
import { e as escape_html } from "../../../../../../chunks/escaping.js";
import "@sveltejs/kit/internal";
import "../../../../../../chunks/exports.js";
import "../../../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../../../chunks/state.svelte.js";
import { p as page, D as DoctorWorkspaceShell } from "../../../../../../chunks/DoctorWorkspaceShell.js";
import "../../../../../../chunks/api.js";
/* empty css                                                                */
import { u as user } from "../../../../../../chunks/stores.js";
import { Chart, registerables } from "chart.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    Chart.register(...registerables);
    let periodType = "weekly";
    let generating = false;
    user.subscribe((value) => {
    });
    page.subscribe((value) => {
      value.params.id;
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Progress Reports",
      subtitle: "Structured reporting for a single patient, including generated report history, baseline comparison, domain summaries, exports, and clinician commentary.",
      eyebrow: "Doctor Report Workspace",
      maxWidth: "1440px",
      children: ($$renderer3) => {
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<section class="state-card svelte-emu5x6"><p>Loading progress reports...</p></section>`);
        }
        $$renderer3.push(`<!--]-->`);
      },
      $$slots: {
        default: true,
        actions: ($$renderer3) => {
          {
            $$renderer3.push(`<button class="outline-btn svelte-emu5x6">Back to Patient</button> `);
            $$renderer3.select(
              { value: periodType, class: "period-select" },
              ($$renderer4) => {
                $$renderer4.option({ value: "weekly" }, ($$renderer5) => {
                  $$renderer5.push(`Weekly`);
                });
                $$renderer4.option({ value: "monthly" }, ($$renderer5) => {
                  $$renderer5.push(`Monthly`);
                });
              },
              "svelte-emu5x6"
            );
            $$renderer3.push(` <button class="primary-btn svelte-emu5x6"${attr("disabled", generating, true)}>${escape_html("Generate Report")}</button>`);
          }
        }
      }
    });
  });
}
export {
  _page as default
};
