import { a as attr_class, c as stringify } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import "../../../../chunks/index3.js";
/* empty css                                                               */
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    let difficulty = 5;
    let earnedBadges = [];
    onDestroy(() => {
    });
    function getDomainColor(domain) {
      const colors = { visual_scanning: "from-purple-500 to-pink-500" };
      return colors[domain] || "from-blue-500 to-purple-500";
    }
    $$renderer2.push(`<div class="mot-container svelte-egvonm">`);
    BadgeNotification($$renderer2, { badges: earnedBadges });
    $$renderer2.push(`<!----> <div class="task-header svelte-egvonm"><div class="header-content svelte-egvonm"><div class="task-badges svelte-egvonm"><span${attr_class(`domain-badge bg-gradient-to-r ${stringify(getDomainColor("visual_scanning"))}`, "svelte-egvonm")}>👁️ Visual Scanning</span> <span class="difficulty-badge svelte-egvonm">Level ${escape_html(difficulty)}</span></div> <h1 class="task-title svelte-egvonm">Multiple Object Tracking</h1> <p class="task-subtitle svelte-egvonm">Dynamic Visual Attention • Pylyshyn &amp; Storm (2006)</p></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="phase-container intro-phase svelte-egvonm"><div class="intro-card svelte-egvonm"><div class="clinical-note svelte-egvonm"><span class="clinical-icon svelte-egvonm">🔬</span> <div class="svelte-egvonm"><div class="clinical-label svelte-egvonm">Clinical Validation</div> <div class="clinical-text svelte-egvonm">Measures sustained visual attention and dynamic tracking ability, 
							relevant for driving safety and real-world multitasking in MS patients.</div></div></div> <div class="instructions-section svelte-egvonm"><h2 class="section-title svelte-egvonm">How This Task Works</h2> <div class="instruction-steps svelte-egvonm"><div class="step-item svelte-egvonm"><div class="step-number svelte-egvonm">1</div> <div class="step-content svelte-egvonm"><div class="step-title svelte-egvonm">Watch the Targets</div> <div class="step-desc svelte-egvonm">Several circles will flash yellow — these are your targets to track</div></div></div> <div class="step-item svelte-egvonm"><div class="step-number svelte-egvonm">2</div> <div class="step-content svelte-egvonm"><div class="step-title svelte-egvonm">Track as They Move</div> <div class="step-desc svelte-egvonm">All circles will move randomly. Keep your eyes on the targets!</div></div></div> <div class="step-item svelte-egvonm"><div class="step-number svelte-egvonm">3</div> <div class="step-content svelte-egvonm"><div class="step-title svelte-egvonm">Select the Targets</div> <div class="step-desc svelte-egvonm">When movement stops, click all the circles you were tracking</div></div></div></div></div> <div class="task-details-grid svelte-egvonm"><div class="detail-card svelte-egvonm"><div class="detail-label svelte-egvonm">Objects</div> <div class="detail-value svelte-egvonm">${escape_html(0)}</div></div> <div class="detail-card svelte-egvonm"><div class="detail-label svelte-egvonm">Targets to Track</div> <div class="detail-value svelte-egvonm">${escape_html(0)}</div></div> <div class="detail-card svelte-egvonm"><div class="detail-label svelte-egvonm">Tracking Time</div> <div class="detail-value svelte-egvonm">${escape_html(0)}s</div></div> <div class="detail-card svelte-egvonm"><div class="detail-label svelte-egvonm">Speed</div> <div class="detail-value svelte-egvonm">${escape_html(1)}×</div></div></div> <button class="start-button svelte-egvonm"><span class="button-icon svelte-egvonm">▶</span> Begin Tracking</button></div></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
