import "clsx";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import { a as attr_class, f as bind_props, c as stringify } from "../../../chunks/index2.js";
/* empty css                                                       */
import { j as fallback } from "../../../chunks/utils3.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import { a as attr } from "../../../chunks/attributes.js";
import { L as LoadingSkeleton } from "../../../chunks/LoadingSkeleton.js";
function EmptyState($$renderer, $$props) {
  let icon = fallback($$props["icon"], "🧠");
  let title = fallback($$props["title"], "No Data Yet");
  let message = fallback($$props["message"], "Get started to see your progress here.");
  let actionText = fallback($$props["actionText"], "Get Started");
  let actionLink = fallback($$props["actionLink"], "/training");
  let tip = fallback($$props["tip"], "");
  let variant = fallback(
    $$props["variant"],
    "default"
    // default, compact, large
  );
  $$renderer.push(`<div${attr_class(`empty-state ${stringify(variant)}`, "svelte-13862ru")}><div class="empty-content svelte-13862ru"><div class="empty-icon svelte-13862ru">${escape_html(icon)}</div> <h3 class="empty-title svelte-13862ru">${escape_html(title)}</h3> <p class="empty-message svelte-13862ru">${escape_html(message)}</p> `);
  if (actionText && actionLink) {
    $$renderer.push("<!--[-->");
    $$renderer.push(`<a${attr("href", actionLink)} class="empty-action svelte-13862ru">${escape_html(actionText)} →</a>`);
  } else {
    $$renderer.push("<!--[!-->");
  }
  $$renderer.push(`<!--]--> `);
  if (tip) {
    $$renderer.push("<!--[-->");
    $$renderer.push(`<div class="empty-tip svelte-13862ru"><span class="tip-icon svelte-13862ru">💡</span> <span class="tip-text svelte-13862ru">${escape_html(tip)}</span></div>`);
  } else {
    $$renderer.push("<!--[!-->");
  }
  $$renderer.push(`<!--]--></div></div>`);
  bind_props($$props, { icon, title, message, actionText, actionLink, tip, variant });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="preview-container svelte-pz3vgw"><div class="preview-header svelte-pz3vgw"><h1 class="svelte-pz3vgw">🎨 Phase 6: Empty States Preview</h1> <p class="svelte-pz3vgw">All empty states and loading skeletons without clearing your data</p> <button class="back-btn svelte-pz3vgw">← Back to Dashboard</button></div> <div class="preview-grid svelte-pz3vgw"><div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Progress Page - No Data</h3> <div class="preview-wrapper gradient-bg svelte-pz3vgw">`);
    EmptyState($$renderer2, {
      icon: "📊",
      title: "Start Your Progress Journey",
      message: "Complete your first training session to see detailed analytics, trends, and badges!",
      actionText: "Begin Training",
      actionLink: "/training",
      tip: "Consistent training leads to measurable cognitive improvements",
      variant: "large"
    });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Session Summary - No Session</h3> <div class="preview-wrapper purple-gradient-bg svelte-pz3vgw">`);
    EmptyState($$renderer2, {
      icon: "🎯",
      title: "No Session Data",
      message: "Complete a training session to see your celebration summary here!",
      actionText: "Start Training",
      actionLink: "/training",
      tip: "Each session includes 4 cognitive tasks designed to challenge your brain"
    });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Weekly Summary - Less than 7 Days</h3> <div class="preview-wrapper svelte-pz3vgw">`);
    EmptyState($$renderer2, {
      icon: "📅",
      title: "Build Your Weekly Streak",
      message: "Train for 7 days to unlock your weekly summary with insights and progress tracking!",
      actionText: "Start Training",
      actionLink: "/training",
      tip: "Training multiple days per week shows better cognitive improvements",
      variant: "compact"
    });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Badges - No Badges Earned</h3> <div class="preview-wrapper svelte-pz3vgw">`);
    EmptyState($$renderer2, {
      icon: "🎯",
      title: "Start Earning Badges!",
      message: "Complete training sessions to unlock your first achievement badge!",
      actionText: "Start Training",
      actionLink: "/training",
      tip: "Badges track your progress, consistency, and mastery across all cognitive domains",
      variant: "compact"
    });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Performance Trends - Not Enough Data</h3> <div class="preview-wrapper svelte-pz3vgw">`);
    EmptyState($$renderer2, {
      icon: "📈",
      title: "Track Your Progress",
      message: "Complete multiple training sessions to unlock your performance trends graph and see how you improve over time!",
      actionText: "Start Training",
      actionLink: "/training",
      tip: "Trends become visible after 3+ sessions",
      variant: "compact"
    });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Loading Skeleton - Card Grid</h3> <div class="preview-wrapper svelte-pz3vgw">`);
    LoadingSkeleton($$renderer2, { variant: "card", count: 4 });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Loading Skeleton - List Items</h3> <div class="preview-wrapper svelte-pz3vgw">`);
    LoadingSkeleton($$renderer2, { variant: "list", count: 3 });
    $$renderer2.push(`<!----></div></div> <div class="preview-section svelte-pz3vgw"><h3 class="svelte-pz3vgw">Loading Skeleton - Block</h3> <div class="preview-wrapper svelte-pz3vgw">`);
    LoadingSkeleton($$renderer2, { variant: "default", count: 2 });
    $$renderer2.push(`<!----></div></div></div> <div class="preview-footer svelte-pz3vgw"><h3 class="svelte-pz3vgw">✅ Phase 6 Features Demonstrated:</h3> <ul class="svelte-pz3vgw"><li class="svelte-pz3vgw">✨ Animated icons with bounce effect</li> <li class="svelte-pz3vgw">🎨 Gradient backgrounds (3 variants: default, compact, large)</li> <li class="svelte-pz3vgw">💡 Glass-morphism tip cards</li> <li class="svelte-pz3vgw">🔘 Interactive call-to-action buttons with hover effects</li> <li class="svelte-pz3vgw">⚡ Shimmer loading skeletons (3 variants: card, list, block)</li> <li class="svelte-pz3vgw">📱 Fully responsive design</li> <li class="svelte-pz3vgw">🎯 Context-specific messaging for each empty state</li> <li class="svelte-pz3vgw">✨ Professional polish throughout</li></ul></div></div>`);
  });
}
export {
  _page as default
};
