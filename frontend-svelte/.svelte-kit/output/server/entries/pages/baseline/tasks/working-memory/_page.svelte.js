import { e as escape_html } from "../../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let nBackLevel = 1;
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="test-container svelte-z6zxfp">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-z6zxfp"><h1 class="svelte-z6zxfp">🧠 Working Memory Test</h1> <h2 style="color: #764ba2; font-size: 1.5rem; margin-bottom: 2rem; font-weight: 600;" class="svelte-z6zxfp">${escape_html(nBackLevel)}-Back Task</h2> <div class="instructions svelte-z6zxfp"><div class="instruction-header svelte-z6zxfp"><h3 class="svelte-z6zxfp">📋 How It Works:</h3></div> <div class="instruction-steps svelte-z6zxfp"><div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">1</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">You'll see <strong class="svelte-z6zxfp">letters</strong> appear one at a time on screen</p></div></div> <div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">2</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">Each letter stays for <strong class="svelte-z6zxfp">2 seconds</strong></p></div></div> <div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">3</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">Click <strong class="match-btn svelte-z6zxfp">✓ Match</strong> if the current letter is the <strong class="svelte-z6zxfp">same</strong> as the letter from <strong class="svelte-z6zxfp">${escape_html(nBackLevel)} step${escape_html("")} ago</strong></p></div></div> <div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">4</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">Click <strong class="no-match-btn svelte-z6zxfp">✗ No Match</strong> if it's different</p></div></div></div> <div class="example-box svelte-z6zxfp"><h4 class="svelte-z6zxfp">💡 Example for ${escape_html(nBackLevel)}-Back:</h4> <div class="sequence-display svelte-z6zxfp"><div class="sequence-item svelte-z6zxfp"><span class="letter-demo svelte-z6zxfp">A</span> <span class="position svelte-z6zxfp">Position 1</span></div> <div class="arrow svelte-z6zxfp">→</div> <div class="sequence-item svelte-z6zxfp"><span class="letter-demo svelte-z6zxfp">B</span> <span class="position svelte-z6zxfp">Position 2</span></div> <div class="arrow svelte-z6zxfp">→</div> <div class="sequence-item highlight svelte-z6zxfp"><span class="letter-demo svelte-z6zxfp">A</span> <span class="position svelte-z6zxfp">Position 3</span> <span class="match-indicator svelte-z6zxfp">✓ MATCH!</span></div></div> <p class="example-explanation svelte-z6zxfp">At position 3, you see <strong class="svelte-z6zxfp">A</strong> again. Looking back ${escape_html(nBackLevel)} step${escape_html("")}, 
						you also saw <strong class="svelte-z6zxfp">A</strong> → Click <strong class="match-btn svelte-z6zxfp">Match</strong>!</p></div> <div class="test-info svelte-z6zxfp"><div class="info-item svelte-z6zxfp"><span class="info-label svelte-z6zxfp">Total Trials:</span> <span class="info-value svelte-z6zxfp">20 letters</span></div> <div class="info-item svelte-z6zxfp"><span class="info-label svelte-z6zxfp">Difficulty:</span> <span class="info-value svelte-z6zxfp">${escape_html(nBackLevel)}-Back</span></div> <div class="info-item svelte-z6zxfp"><span class="info-label svelte-z6zxfp">Time per Letter:</span> <span class="info-value svelte-z6zxfp">2 seconds</span></div></div></div> <div class="button-group svelte-z6zxfp"><button class="btn-primary btn-large svelte-z6zxfp">🚀 Start Test</button> <button class="btn-secondary svelte-z6zxfp">← Back to Dashboard</button></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
