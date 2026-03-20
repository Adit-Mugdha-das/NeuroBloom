import { Y as head } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    head("1covncy", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Inspection Time - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="task-container svelte-1covncy">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="instructions-panel svelte-1covncy"><div class="task-header svelte-1covncy"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;" class="svelte-1covncy"><h1 class="svelte-1covncy">🔍 Inspection Time Task</h1> `);
          DifficultyBadge($$renderer2, {
            difficulty: 5,
            domain: "Processing Speed"
          });
          $$renderer2.push(`<!----></div> <p class="task-subtitle svelte-1covncy">Pure Perceptual Speed Assessment</p></div> <div class="clinical-context svelte-1covncy"><h3 class="svelte-1covncy">📋 About This Task</h3> <p class="svelte-1covncy">The Inspection Time task measures your brain's pure perceptual processing speed - how quickly you can perceive and identify visual information.</p> <div class="ms-benefits svelte-1covncy"><h4 class="svelte-1covncy">✨ Benefits for MS</h4> <ul class="svelte-1covncy"><li class="svelte-1covncy"><strong class="svelte-1covncy">No Motor Component:</strong> Tests pure perception, not movement speed</li> <li class="svelte-1covncy"><strong class="svelte-1covncy">Processing Speed:</strong> Fundamental to many cognitive abilities</li> <li class="svelte-1covncy"><strong class="svelte-1covncy">Visual Pathways:</strong> Directly assesses visual processing efficiency</li> <li class="svelte-1covncy"><strong class="svelte-1covncy">Adaptive Training:</strong> Adjusts to your perceptual threshold</li></ul></div> <div class="research-note svelte-1covncy"><strong class="svelte-1covncy">Research Foundation:</strong> Based on Vickers &amp; Smith (1986) perceptual speed research. Widely used in cognitive aging and clinical neuropsychology.</div></div> <div class="how-it-works svelte-1covncy"><h3 class="svelte-1covncy">🎯 How It Works</h3> <div class="instruction-steps svelte-1covncy"><div class="step svelte-1covncy"><span class="step-number svelte-1covncy">1</span> <div class="step-content svelte-1covncy"><h4 class="svelte-1covncy">Brief Flash</h4> <p class="svelte-1covncy">Two vertical lines will appear very briefly (as short as 50 milliseconds)</p></div></div> <div class="step svelte-1covncy"><span class="step-number svelte-1covncy">2</span> <div class="step-content svelte-1covncy"><h4 class="svelte-1covncy">Immediate Mask</h4> <p class="svelte-1covncy">A pattern mask appears immediately to prevent afterimage processing</p></div></div> <div class="step svelte-1covncy"><span class="step-number svelte-1covncy">3</span> <div class="step-content svelte-1covncy"><h4 class="svelte-1covncy">Your Decision</h4> <p class="svelte-1covncy">Indicate which line was longer: LEFT or RIGHT</p></div></div></div> <div class="important-note svelte-1covncy"><strong class="svelte-1covncy">⏱️ Important:</strong> The flash is VERY brief - this is intentional! We're measuring your basic perceptual speed. Don't worry if it seems fast; everyone finds this challenging.</div></div> <div class="instruction-tips svelte-1covncy"><h3 class="svelte-1covncy">💡 Tips for Success</h3> <ul class="svelte-1covncy"><li class="svelte-1covncy">Focus on the center of the screen before each trial</li> <li class="svelte-1covncy">Trust your first impression - don't overthink</li> <li class="svelte-1covncy">The presentation is too brief for detailed analysis</li> <li class="svelte-1covncy">It's okay to guess if you're not sure</li> <li class="svelte-1covncy">Relax - this measures perception, not intelligence</li></ul></div> <div class="action-buttons svelte-1covncy"><button class="primary-btn svelte-1covncy">Start Practice Trials</button> <button class="help-btn svelte-1covncy">📖 More Information</button></div></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
