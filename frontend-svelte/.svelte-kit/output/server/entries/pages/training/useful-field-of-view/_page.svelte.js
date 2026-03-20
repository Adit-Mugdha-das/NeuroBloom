import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import "../../../../chunks/api.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let difficulty = 1;
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="ufov-container svelte-idketv"><div class="ufov-header svelte-idketv"><button class="back-button svelte-idketv">← Back to Dashboard</button> <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;" class="svelte-idketv"><h1 class="svelte-idketv">Useful Field of View (UFOV)</h1> `);
    DifficultyBadge($$renderer2, { difficulty, domain: "Visual Scanning" });
    $$renderer2.push(`<!----></div> <div class="clinical-badge svelte-idketv"><span class="badge-icon svelte-idketv">🚗</span> <span class="badge-text svelte-idketv">Driving Safety Assessment</span></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="intro-section svelte-idketv"><div class="intro-card svelte-idketv"><h2 class="svelte-idketv">Visual Processing &amp; Divided Attention</h2> <p class="intro-description svelte-idketv">The Useful Field of View (UFOV) test measures your ability to quickly process 
					visual information and divide your attention across your visual field. This is 
					a critical skill for safe driving and everyday activities.</p> <div class="clinical-validation svelte-idketv"><h3 class="svelte-idketv">📋 Clinical Validation</h3> <p class="svelte-idketv"><strong class="svelte-idketv">Ball et al., 1993</strong> - Predicts driving safety and crash risk</p> <p class="svelte-idketv">Widely used in MS research to assess visual processing deficits</p></div> <div class="instructions-grid svelte-idketv"><div class="instruction-item svelte-idketv"><div class="instruction-number svelte-idketv">1</div> <div class="instruction-content svelte-idketv"><h4 class="svelte-idketv">Focus on the Center</h4> <p class="svelte-idketv">A fixation cross (+) will appear. Keep your eyes focused on the center.</p></div></div> <div class="instruction-item svelte-idketv"><div class="instruction-number svelte-idketv">2</div> <div class="instruction-content svelte-idketv"><h4 class="svelte-idketv">Brief Display</h4> <p class="svelte-idketv">Images will flash very briefly (150-800ms). Process them quickly!</p></div></div> <div class="instruction-item svelte-idketv"><div class="instruction-number svelte-idketv">3</div> <div class="instruction-content svelte-idketv"><h4 class="svelte-idketv">Identify Targets</h4> <p class="svelte-idketv">Report what you saw in the center and/or periphery based on the task.</p></div></div></div> <div class="task-details svelte-idketv"><h3 class="svelte-idketv">Three Subtests:</h3> <div class="subtest-list svelte-idketv"><div class="subtest-item svelte-idketv"><span class="subtest-icon svelte-idketv">⚡</span> <div class="svelte-idketv"><strong class="svelte-idketv">Central ID Only</strong> <p class="svelte-idketv">Identify vehicle in center (car or truck) - Tests processing speed</p></div></div> <div class="subtest-item svelte-idketv"><span class="subtest-icon svelte-idketv">👀</span> <div class="svelte-idketv"><strong class="svelte-idketv">Central + Peripheral</strong> <p class="svelte-idketv">Identify center vehicle AND locate peripheral shape - Tests divided attention</p></div></div> <div class="subtest-item svelte-idketv"><span class="subtest-icon svelte-idketv">🎯</span> <div class="svelte-idketv"><strong class="svelte-idketv">With Distractors</strong> <p class="svelte-idketv">Same as above but with visual clutter - Tests selective attention</p></div></div></div></div> <div class="progress-info svelte-idketv"><p class="svelte-idketv">Complete <strong class="svelte-idketv">10 trials</strong> to finish this session</p> <p class="difficulty-level svelte-idketv">Current Level: <strong class="svelte-idketv">${escape_html(difficulty)}</strong>/10</p></div> <button class="start-button svelte-idketv">Begin UFOV Assessment</button></div></div>`);
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
