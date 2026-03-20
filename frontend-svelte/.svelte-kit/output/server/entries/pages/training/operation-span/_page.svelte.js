import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
/* empty css                                                               */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<!---->const lettersCorrect = JSON.stringify(userLetters) === JSON.stringify(currentTrial.correct_letters);
		const mathCorrect = mathResponses.every((response, i) => response === currentTrial.items[i].is_correct);
		return lettersCorrect &amp;&amp; mathCorrect;
				currentTrialIndex++; <div class="ospan-container svelte-x81epw">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-x81epw"><div class="spinner svelte-x81epw"></div> <p class="svelte-x81epw">Loading Operation Span Task...</p></div>`);
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
