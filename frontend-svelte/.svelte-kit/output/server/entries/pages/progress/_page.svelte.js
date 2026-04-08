import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { c as calculateOverallScore, a as calculateTrendDelta, f as formatPointChange, g as getClinicalStatusTone, b as getClinicalStatusLabel, d as getDomainName, e as calculateBaselineDifficulty } from "../../../chunks/progress.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let comparisonEntries;
    user.subscribe((value) => {
    });
    calculateOverallScore();
    calculateTrendDelta();
    comparisonEntries = Object.entries({});
    comparisonEntries.map(([domain, values]) => ({
      domain,
      label: getDomainName(domain),
      status: getClinicalStatusLabel(values.improvement),
      tone: getClinicalStatusTone(values.improvement),
      pointChange: formatPointChange(values.improvement)
    }));
    comparisonEntries.map(([domain, values]) => {
      const baselineDifficulty = calculateBaselineDifficulty(values.baseline);
      const currentDifficulty = baselineDifficulty;
      const delta = currentDifficulty - baselineDifficulty;
      return {
        domain,
        label: getDomainName(domain),
        baselineDifficulty,
        currentDifficulty,
        delta
      };
    }).filter((entry) => entry.delta !== 0).sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta));
    $$renderer2.push(`<div class="progress-panel svelte-12lluz7">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="state-panel glass-card svelte-12lluz7"><p class="svelte-12lluz7">Loading progress overview...</p></section>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
