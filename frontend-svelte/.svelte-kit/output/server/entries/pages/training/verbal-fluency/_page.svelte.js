import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
/* empty css                                                               */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let earnedBadges = [];
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;"><div style="max-width: 900px; margin: 0 auto;">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);"><div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div> <h2 style="color: #667eea;">Loading Verbal Fluency Task...</h2></div>`);
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
