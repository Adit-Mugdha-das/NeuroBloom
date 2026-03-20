import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import { o as onDestroy } from "../../../../chunks/index-server.js";
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
    onDestroy(() => {
    });
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px;" class="svelte-gkakf1"><div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 800px;" class="svelte-gkakf1"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;" class="svelte-gkakf1"><h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;" class="svelte-gkakf1">Plus-Minus Task</h1> `);
    DifficultyBadge($$renderer2, { difficulty: 5, domain: "Cognitive Flexibility" });
    $$renderer2.push(`<!----></div> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="svelte-gkakf1"><h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;" class="svelte-gkakf1">Cognitive Flexibility Assessment</h2> <p style="font-size: 16px; color: #555; margin-bottom: 15px;" class="svelte-gkakf1">The Plus-Minus Task measures your ability to:</p> <ul style="margin-left: 30px; margin-bottom: 20px; color: #555;" class="svelte-gkakf1"><li style="margin-bottom: 8px;" class="svelte-gkakf1">Switch between mental operations</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">Maintain accuracy under cognitive load</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">Adapt to alternating task demands</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">Process numerical information quickly</li></ul> <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;" class="svelte-gkakf1"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;" class="svelte-gkakf1">How It Works</h3> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-gkakf1"><strong class="svelte-gkakf1">Block A:</strong> Add 3 to each number shown (baseline speed)</p> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-gkakf1"><strong class="svelte-gkakf1">Block B:</strong> Subtract 3 from each number (baseline speed)</p> <p style="font-size: 14px; color: #555;" class="svelte-gkakf1"><strong class="svelte-gkakf1">Block C:</strong> Alternate between +3 and -3 based on the cue (measures switching cost)</p></div> <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;" class="svelte-gkakf1"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;" class="svelte-gkakf1">Instructions</h3> <ul style="margin-left: 20px; color: #555;" class="svelte-gkakf1"><li style="margin-bottom: 8px;" class="svelte-gkakf1">Perform the operation shown and type your answer</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">Press Enter or click Submit after each answer</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">In Block C, pay close attention to the cue (+3 or -3)</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">Work as quickly and accurately as possible</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">Total trials: ${escape_html("36")}</li></ul></div> <div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;" class="svelte-gkakf1"><p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;" class="svelte-gkakf1"><strong class="svelte-gkakf1">Current Difficulty:</strong> Level ${escape_html(difficulty)} / 10</p> <p style="font-size: 13px; color: #0369a1;" class="svelte-gkakf1">`);
          {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`Single digit numbers, clear cues (2 seconds)`);
          }
          $$renderer2.push(`<!--]--></p></div> <button style="padding: 15px 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" class="svelte-gkakf1">Start Test</button></div>`);
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
