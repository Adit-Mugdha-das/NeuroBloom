import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let difficulty = 1;
    let newBadges = [];
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;" class="svelte-yzdviz"><div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 1000px;" class="svelte-yzdviz"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;" class="svelte-yzdviz"><h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;" class="svelte-yzdviz">Dimensional Change Card Sort (DCCS)</h1> `);
    DifficultyBadge($$renderer2, { difficulty: 5, domain: "Cognitive Flexibility" });
    $$renderer2.push(`<!----></div> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="svelte-yzdviz"><h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;" class="svelte-yzdviz">Cognitive Flexibility Assessment</h2> <p style="font-size: 16px; color: #555; margin-bottom: 15px;" class="svelte-yzdviz">The Dimensional Change Card Sort (DCCS) measures your ability to:</p> <ul style="margin-left: 30px; margin-bottom: 20px; color: #555;" class="svelte-yzdviz"><li style="margin-bottom: 8px;" class="svelte-yzdviz">Switch between different sorting rules</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">Adapt to changing task demands</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">Maintain focus during rule changes</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">Inhibit previous responses</li></ul> <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;" class="svelte-yzdviz"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;" class="svelte-yzdviz">How It Works</h3> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-yzdviz"><strong class="svelte-yzdviz">Phase 1:</strong> Sort cards by COLOR (e.g., red cards go to one pile, blue to another)</p> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-yzdviz"><strong class="svelte-yzdviz">Phase 2:</strong> Sort cards by SHAPE (e.g., circles go to one pile, stars to another)</p> <p style="font-size: 14px; color: #555;" class="svelte-yzdviz"><strong class="svelte-yzdviz">Phase 3:</strong> Mixed sorting - a cue will tell you which rule to use on each trial</p></div> <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;" class="svelte-yzdviz"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;" class="svelte-yzdviz">Instructions</h3> <ul style="margin-left: 20px; color: #555;" class="svelte-yzdviz"><li style="margin-bottom: 8px;" class="svelte-yzdviz">Click on the target card that matches the test card</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">In Phase 3, pay attention to the cue shown before each card</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">Work as quickly and accurately as possible</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">Total trials: ${escape_html("40")}</li></ul></div> <div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;" class="svelte-yzdviz"><p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;" class="svelte-yzdviz"><strong class="svelte-yzdviz">Current Difficulty:</strong> Level ${escape_html(difficulty)} / 10</p> <p style="font-size: 13px; color: #0369a1;" class="svelte-yzdviz">`);
          {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`Basic: Color &amp; Shape sorting, ${escape_html(1500)}ms cues`);
          }
          $$renderer2.push(`<!--]--></p> `);
          {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--></div> <button style="padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" class="svelte-yzdviz">Start Test</button></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    if (newBadges && newBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: newBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
