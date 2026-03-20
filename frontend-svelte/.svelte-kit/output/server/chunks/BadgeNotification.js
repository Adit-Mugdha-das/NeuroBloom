import { _ as bind_props } from "./index2.js";
import { j as fallback } from "./utils2.js";
/* empty css                                                */
function BadgeNotification($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let badges = fallback($$props["badges"], () => [], true);
    let currentBadgeIndex = 0;
    badges[currentBadgeIndex];
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { badges });
  });
}
export {
  BadgeNotification as B
};
