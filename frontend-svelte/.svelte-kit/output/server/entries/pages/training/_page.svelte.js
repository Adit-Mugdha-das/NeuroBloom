import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { B as BadgeNotification } from "../../../chunks/BadgeNotification.js";
import { u as user } from "../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let sessionConstraints, sessionPacing;
    let newlyEarnedBadges = [];
    user.subscribe((value) => {
    });
    function formatDuration(seconds) {
      const totalSeconds = Math.max(0, Number(seconds) || 0);
      const minutes = Math.floor(totalSeconds / 60);
      const remainingSeconds = totalSeconds % 60;
      if (minutes <= 0) return `${remainingSeconds} sec`;
      if (remainingSeconds === 0) return `${minutes} min`;
      return `${minutes} min ${remainingSeconds} sec`;
    }
    sessionConstraints = null;
    sessionPacing = null;
    !sessionPacing ? null : sessionPacing.current_session_in_progress ? {
      kind: "info",
      title: "Session in progress",
      message: `You have ${0} of ${sessionConstraints?.tasks_per_session || 4} tasks done in this session. Finish the remaining tasks whenever you are ready.`
    } : sessionPacing.remaining_sessions_today === 0 ? {
      kind: "warning",
      title: "Daily limit reached",
      message: `You have completed ${sessionConstraints?.max_sessions_per_day || 3} sessions today. NeuroBloom is holding the next session until tomorrow to protect recovery.`
    } : sessionPacing.cooldown_active ? {
      kind: "warning",
      title: "Cooldown in effect",
      message: `Your next session becomes available in ${formatDuration(sessionPacing.cooldown_remaining_seconds)}.`
    } : null;
    $$renderer2.push(`<div class="training-shell svelte-d816z7">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (newlyEarnedBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: newlyEarnedBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="training-layout svelte-d816z7">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="state-card svelte-d816z7"><p>Loading your training plan...</p></section>`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
  });
}
export {
  _page as default
};
