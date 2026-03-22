import { u as unsubscribe_stores, s as store_get } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import { e as escape_html } from "../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../chunks/state.svelte.js";
import "../../../chunks/api.js";
import { t as translateText, l as locale } from "../../../chunks/index3.js";
import { u as user } from "../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let primaryRecommendation;
    let currentUser = null;
    user.subscribe((value) => {
      currentUser = value;
    });
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function getDomainName(domain) {
      const names = {
        working_memory: t("Working Memory"),
        attention: t("Attention"),
        flexibility: t("Cognitive Flexibility"),
        planning: t("Planning"),
        processing_speed: t("Processing Speed"),
        visual_scanning: t("Visual Scanning")
      };
      return names[domain] || t("Training");
    }
    function getDisplayName() {
      return currentUser?.fullName || currentUser?.full_name || currentUser?.email || "Patient";
    }
    function getPrimaryRecommendation() {
      return null;
    }
    function getEncouragementMessage() {
      if (primaryRecommendation?.domain) {
        if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
          return `দারুণ অগ্রগতি! আপনি এই সপ্তাহে ${getDomainName(primaryRecommendation.domain)} আরও শক্তিশালী করছেন।`;
        }
        return `Great progress! You're improving your ${getDomainName(primaryRecommendation.domain).toLowerCase()} this week.`;
      }
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "দারুণ অগ্রগতি! প্রতিটি ট্রেনিং সেশন আপনার কগনিটিভ স্বাস্থ্যের আরও পরিষ্কার চিত্র গড়ে তুলতে সাহায্য করে।" : "Great progress! Each training session helps build a clearer picture of your cognitive health.";
    }
    primaryRecommendation = getPrimaryRecommendation();
    [
      {
        key: "sessions",
        label: t("Total Sessions"),
        value: t("Unavailable"),
        tone: "indigo"
      },
      {
        key: "domains",
        label: t("Active Domains"),
        value: t("Unavailable"),
        tone: "cyan"
      },
      {
        key: "last-training",
        label: t("Last Training"),
        value: t("Unavailable"),
        tone: "violet"
      },
      {
        key: "streak",
        label: t("Current Streak"),
        value: t("Unavailable"),
        tone: "teal"
      }
    ];
    getEncouragementMessage();
    $$renderer2.push(`<div class="dashboard-shell svelte-x1i5gj">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <header class="topbar svelte-x1i5gj"><div class="brand-block svelte-x1i5gj"><p class="eyebrow svelte-x1i5gj">NeuroBloom</p> <h1 class="svelte-x1i5gj">Your Brain Health Today</h1> <p class="subcopy svelte-x1i5gj">A calm view of your training progress, next step, and care support.</p></div> <div class="topbar-actions svelte-x1i5gj">`);
    if (currentUser) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="user-email svelte-x1i5gj">${escape_html(getDisplayName())}</span> <button class="ghost-btn svelte-x1i5gj">Notifications `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></button> <button class="ghost-btn svelte-x1i5gj">Messages</button> <button class="ghost-btn svelte-x1i5gj">Settings</button>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <button class="logout-btn svelte-x1i5gj">Logout</button></div></header> <main class="dashboard-main svelte-x1i5gj">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<section class="loading-panel svelte-x1i5gj"><p>Loading your dashboard...</p></section>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
