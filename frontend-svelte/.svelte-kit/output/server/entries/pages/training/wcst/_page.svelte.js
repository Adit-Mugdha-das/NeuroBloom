import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
/* empty css                                                                 */
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let difficulty = 1;
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="container"><div style="background: white; padding: 30px; border-radius: 10px; margin: 20px auto; max-width: 1000px;"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;"><h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;">Wisconsin Card Sorting Test</h1> `);
    DifficultyBadge($$renderer2, { difficulty: 5, domain: "Cognitive Flexibility" });
    $$renderer2.push(`<!----></div> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div><h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;">Executive Function Assessment</h2> <p style="font-size: 16px; color: #555; margin-bottom: 15px;">The Wisconsin Card Sorting Test (WCST) measures your ability to:</p> <ul style="margin-left: 30px; margin-bottom: 20px; color: #555;"><li style="margin-bottom: 8px;"><strong>Shift mental sets</strong> - Adapt when rules change</li> <li style="margin-bottom: 8px;"><strong>Learn from feedback</strong> - Use "Correct" or "Wrong" cues</li> <li style="margin-bottom: 8px;"><strong>Maintain strategies</strong> - Stick with a rule once discovered</li> <li style="margin-bottom: 8px;"><strong>Recognize patterns</strong> - Identify sorting rules quickly</li></ul> <div style="background: #e6f3ff; border: 2px solid #99ccff; padding: 15px; border-radius: 8px; margin-bottom: 15px;"><h3 style="font-weight: 600; color: #0066cc; margin-bottom: 8px;">How It Works:</h3> <p style="color: #0066cc;">You'll see a card with a color, shape, and number of symbols. Sort it into one of
						four piles by clicking a target card. The sorting rule (color, shape, or number)
						will change without warning. Use the feedback to discover the current rule.</p></div> <p style="color: #666; margin-bottom: 20px;"><strong>Current Difficulty:</strong> Level ${escape_html(difficulty)}/10</p> <button style="width: 100%; padding: 15px; background: #0066cc; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">Continue to Instructions</button></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
  });
}
export {
  _page as default
};
