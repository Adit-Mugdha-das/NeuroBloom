import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { u as user } from "../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let primaryRecommendation;
    let currentUser = null;
    user.subscribe((value) => {
      currentUser = value;
    });
    function getDomainName(domain) {
      const names = {
        working_memory: "Working Memory",
        attention: "Attention",
        flexibility: "Cognitive Flexibility",
        planning: "Planning",
        processing_speed: "Processing Speed",
        visual_scanning: "Visual Scanning"
      };
      return names[domain] || "Training";
    }
    function getDisplayName() {
      return currentUser?.fullName || currentUser?.full_name || currentUser?.email || "Patient";
    }
    function getPrimaryRecommendation() {
      return null;
    }
    function getEncouragementMessage() {
      if (primaryRecommendation?.domain) {
        return `Great progress! You're improving your ${getDomainName(primaryRecommendation.domain).toLowerCase()} this week.`;
      }
      return "Great progress! Each training session helps build a clearer picture of your cognitive health.";
    }
    primaryRecommendation = getPrimaryRecommendation();
    getEncouragementMessage();
    $$renderer2.push(`<div class="dashboard-shell svelte-x1i5gj">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <header class="topbar svelte-x1i5gj"><div class="brand-block svelte-x1i5gj"><p class="eyebrow svelte-x1i5gj">NeuroBloom</p> <h1 class="svelte-x1i5gj">Your Brain Health Today</h1> <p class="subcopy svelte-x1i5gj">A calm view of your training progress, next step, and care support.</p></div> <div class="topbar-actions svelte-x1i5gj">`);
    if (currentUser) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="user-email svelte-x1i5gj">${escape_html(getDisplayName())}</span> <button class="ghost-btn svelte-x1i5gj">Notifications `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></button> <button class="ghost-btn svelte-x1i5gj">Messages</button> <button class="ghost-btn svelte-x1i5gj">Settings</button>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <button class="logout-btn svelte-x1i5gj">Logout</button></div></header> <main class="dashboard-main svelte-x1i5gj">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="loading-panel svelte-x1i5gj"><p>Loading your dashboard...</p></section>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
  });
}
export {
  _page as default
};
