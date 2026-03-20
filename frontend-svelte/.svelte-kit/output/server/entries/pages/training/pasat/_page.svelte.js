import { Y as head } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    user.subscribe((value) => {
    });
    head("1jl478t", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>PASAT - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="task-container svelte-1jl478t">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="instructions-panel svelte-1jl478t"><div class="task-header svelte-1jl478t"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;"><h1 class="svelte-1jl478t">🎯 PASAT (Paced Auditory Serial Addition Test)</h1> `);
          DifficultyBadge($$renderer2, {
            difficulty: 5,
            domain: "Processing Speed"
          });
          $$renderer2.push(`<!----></div> <p class="task-subtitle svelte-1jl478t">MS Gold Standard Attention Assessment</p> <div class="gold-standard-badge svelte-1jl478t">⭐⭐⭐⭐⭐ CLINICAL GOLD STANDARD</div></div> <div class="clinical-context svelte-1jl478t"><h3 class="svelte-1jl478t">📋 About This Task</h3> <p>PASAT is the most widely used cognitive test in MS research and clinical trials. It measures sustained attention, working memory, and processing speed under time pressure.</p> <div class="ms-benefits svelte-1jl478t"><h4 class="svelte-1jl478t">✨ Why PASAT is Critical for MS</h4> <ul class="svelte-1jl478t"><li class="svelte-1jl478t"><strong>Historical Standard:</strong> Used in MS trials for decades</li> <li class="svelte-1jl478t"><strong>Sustained Attention:</strong> Tracks attention over extended periods</li> <li class="svelte-1jl478t"><strong>Lesion Correlation:</strong> Performance correlates with brain lesion burden</li> <li class="svelte-1jl478t"><strong>Functional Predictor:</strong> Relates to real-world cognitive abilities</li></ul></div> <div class="research-note svelte-1jl478t"><strong>Research Foundation:</strong> Gronwall, 1977 - Paced Auditory Serial-Addition Task. Extensively validated in MS populations worldwide.</div></div> <div class="how-it-works svelte-1jl478t"><h3 class="svelte-1jl478t">🎯 How It Works</h3> <div class="pasat-example svelte-1jl478t"><div class="example-header svelte-1jl478t">Example:</div> <div class="example-sequence svelte-1jl478t"><div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">3</div> <div class="action svelte-1jl478t">(Remember this)</div></div> <div class="arrow svelte-1jl478t">→</div> <div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">5</div> <div class="action svelte-1jl478t">Answer: <strong>8</strong></div> <div class="explanation svelte-1jl478t">(3 + 5 = 8)</div></div> <div class="arrow svelte-1jl478t">→</div> <div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">2</div> <div class="action svelte-1jl478t">Answer: <strong>7</strong></div> <div class="explanation svelte-1jl478t">(5 + 2 = 7)</div></div> <div class="arrow svelte-1jl478t">→</div> <div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">9</div> <div class="action svelte-1jl478t">Answer: <strong>11</strong></div> <div class="explanation svelte-1jl478t">(2 + 9 = 11)</div></div></div></div> <div class="key-rule svelte-1jl478t"><strong>⚠️ KEY RULE:</strong> Add each NEW digit to the PREVIOUS digit. Ignore the running total!</div> <div class="instruction-steps svelte-1jl478t"><div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">1</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">See the Digit</h4> <p class="svelte-1jl478t">A single digit (1-9) appears on screen</p></div></div> <div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">2</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">Add to Previous</h4> <p class="svelte-1jl478t">Add this digit to the one you just saw (not the answer you gave!)</p></div></div> <div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">3</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">Type Your Answer</h4> <p class="svelte-1jl478t">Enter the sum and press Enter before the next digit appears</p></div></div> <div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">4</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">Maintain Pace</h4> <p class="svelte-1jl478t">Keep going! Digits appear every ${escape_html(3)} seconds</p></div></div></div></div> <div class="instruction-tips svelte-1jl478t"><h3 class="svelte-1jl478t">💡 Tips for Success</h3> <ul class="svelte-1jl478t"><li class="svelte-1jl478t"><strong>Focus on the previous digit</strong> - not your last answer</li> <li class="svelte-1jl478t"><strong>Don't try to keep a running total</strong> - that's not the task</li> <li class="svelte-1jl478t"><strong>Speed matters</strong> - try to answer before the next digit</li> <li class="svelte-1jl478t"><strong>If you miss one, keep going</strong> - don't get discouraged</li> <li class="svelte-1jl478t"><strong>Stay calm</strong> - this is challenging even for healthy adults</li> <li class="svelte-1jl478t"><strong>It's okay to skip</strong> - better to wait for the next digit than lose track</li></ul></div> <div class="difficulty-info svelte-1jl478t"><h4 class="svelte-1jl478t">📊 Your Current Pace</h4> <p><strong>${escape_html(3)} seconds</strong> between digits</p> <p class="difficulty-description svelte-1jl478t">${escape_html("Standard PASAT-3")}</p></div> <div class="action-buttons svelte-1jl478t"><button class="primary-btn svelte-1jl478t">Start Practice (4 digits)</button> <button class="help-btn svelte-1jl478t">📖 More Information</button></div></div>`);
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
