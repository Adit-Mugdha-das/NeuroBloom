import { u as unsubscribe_stores, s as store_get } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { t as translateText, l as locale, a as localeText, f as formatNumber } from "../../../../chunks/index3.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    let newBadges = [];
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function difficultySummary() {
      {
        return lt("Single digit numbers, clear cues (2 seconds)", "এক অঙ্কের সংখ্যা, স্পষ্ট সংকেত (২ সেকেন্ড)");
      }
    }
    user.subscribe((value) => {
    });
    onDestroy(() => {
    });
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px;" data-localize-skip="" class="svelte-gkakf1"><div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 800px;" class="svelte-gkakf1"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;" class="svelte-gkakf1"><h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;" class="svelte-gkakf1">${escape_html(t("Plus-Minus Task"))}</h1> `);
    DifficultyBadge($$renderer2, { difficulty, domain: "Cognitive Flexibility" });
    $$renderer2.push(`<!----></div> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="svelte-gkakf1"><h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;" class="svelte-gkakf1">${escape_html(t("Cognitive Flexibility Assessment"))}</h2> <p style="font-size: 16px; color: #555; margin-bottom: 15px;" class="svelte-gkakf1">${escape_html(t("The Plus-Minus Task measures your ability to:"))}</p> <ul style="margin-left: 30px; margin-bottom: 20px; color: #555;" class="svelte-gkakf1"><li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Switch between mental operations"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Maintain accuracy under cognitive load"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Adapt to alternating task demands"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Process numerical information quickly"))}</li></ul> <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;" class="svelte-gkakf1"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;" class="svelte-gkakf1">${escape_html(t("How It Works"))}</h3> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-gkakf1"><strong class="svelte-gkakf1">${escape_html(t("Block A:"))}</strong> ${escape_html(t("Add 3 to each number shown (baseline speed)"))}</p> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-gkakf1"><strong class="svelte-gkakf1">${escape_html(t("Block B:"))}</strong> ${escape_html(t("Subtract 3 from each number (baseline speed)"))}</p> <p style="font-size: 14px; color: #555;" class="svelte-gkakf1"><strong class="svelte-gkakf1">${escape_html(t("Block C:"))}</strong> ${escape_html(t("Alternate between +3 and -3 based on the cue (measures switching cost)"))}</p></div> <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;" class="svelte-gkakf1"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;" class="svelte-gkakf1">${escape_html(t("Instructions"))}</h3> <ul style="margin-left: 20px; color: #555;" class="svelte-gkakf1"><li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Perform the operation shown and type your answer"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Press Enter or click Submit after each answer"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("In Block C, pay close attention to the cue (+3 or -3)"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(t("Work as quickly and accurately as possible"))}</li> <li style="margin-bottom: 8px;" class="svelte-gkakf1">${escape_html(lt(`Total trials: ${"36"}`, `মোট ট্রায়াল: ${n(36)}`))}</li></ul></div> <div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;" class="svelte-gkakf1"><p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;" class="svelte-gkakf1"><strong class="svelte-gkakf1">${escape_html(t("Current Difficulty:"))}</strong> ${escape_html(lt(`Level ${difficulty} / 10`, `লেভেল ${n(difficulty)} / ১০`))}</p> <p style="font-size: 13px; color: #0369a1;" class="svelte-gkakf1">${escape_html(difficultySummary())}</p></div> <button style="padding: 15px 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" class="svelte-gkakf1">${escape_html(t("Start Test"))}</button></div>`);
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
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
