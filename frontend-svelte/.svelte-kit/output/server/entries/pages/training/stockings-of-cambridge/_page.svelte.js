import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { u as user } from "../../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let difficulty = 1;
    let earnedBadges = [];
    user.subscribe((value) => {
      if (value) {
        value.id;
      }
    });
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 2rem;"><div style="max-width: 1000px; margin: 0 auto;">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);"><div style="text-align: center; margin-bottom: 2rem;"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;"><h1 style="font-size: 2.5rem; color: #8b5cf6; margin: 0; font-weight: 700;">🧦 Stockings of Cambridge</h1> `);
      DifficultyBadge($$renderer2, { difficulty, domain: "Executive Planning" });
      $$renderer2.push(`<!----></div> <p style="font-size: 1.1rem; color: #64748b;">Executive Planning &amp; Problem Solving</p></div> <div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border-left: 4px solid #8b5cf6;"><h3 style="color: #1e293b; margin-bottom: 1rem; font-size: 1.3rem;">📋 How It Works</h3> <ul style="color: #475569; line-height: 1.8; margin-left: 1.5rem;"><li><strong>Planning Phase:</strong> Study the start and goal configurations</li> <li><strong>Mental Planning:</strong> Figure out the minimum moves needed</li> <li><strong>Execution:</strong> Move colored balls between stockings to match the goal</li> <li><strong>Constraints:</strong> Stocking 1 holds 3 balls, Stocking 2 holds 2, Stocking 3 holds 1</li> <li><strong>Rule:</strong> Only move the top ball from each stocking</li></ul></div> `);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div style="text-align: center; padding: 2rem; color: #64748b;"><div style="font-size: 2rem; margin-bottom: 1rem;">⏳</div> <p>Loading session...</p></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    if (earnedBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: earnedBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
