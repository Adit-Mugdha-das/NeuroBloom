import { u as unsubscribe_stores, s as store_get } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { t as translateText, l as locale, f as formatNumber } from "../../../../chunks/index3.js";
/* empty css                                                                 */
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function levelLabel(value = difficulty, max = 10) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `লেভেল ${n(value)}/${n(max)}` : `Level ${value}/${max}`;
    }
    $$renderer2.push(`<div class="container" data-localize-skip=""><div style="background: white; padding: 30px; border-radius: 10px; margin: 20px auto; max-width: 1000px;"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;"><h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;">${escape_html(t("Wisconsin Card Sorting Test"))}</h1> `);
    DifficultyBadge($$renderer2, { difficulty: 5, domain: "Cognitive Flexibility" });
    $$renderer2.push(`<!----></div> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div><h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;">${escape_html(t("Executive Function Assessment"))}</h2> <p style="font-size: 16px; color: #555; margin-bottom: 15px;">${escape_html(t("The Wisconsin Card Sorting Test (WCST) measures your ability to:"))}</p> <ul style="margin-left: 30px; margin-bottom: 20px; color: #555;"><li style="margin-bottom: 8px;"><strong>${escape_html(t("Shift mental sets"))}</strong> - ${escape_html(t("Adapt when rules change"))}</li> <li style="margin-bottom: 8px;"><strong>${escape_html(t("Learn from feedback"))}</strong> - ${escape_html(t('Use "Correct" or "Wrong" cues'))}</li> <li style="margin-bottom: 8px;"><strong>${escape_html(t("Maintain strategies"))}</strong> - ${escape_html(t("Stick with a rule once discovered"))}</li> <li style="margin-bottom: 8px;"><strong>${escape_html(t("Recognize patterns"))}</strong> - ${escape_html(t("Identify sorting rules quickly"))}</li></ul> <div style="background: #e6f3ff; border: 2px solid #99ccff; padding: 15px; border-radius: 8px; margin-bottom: 15px;"><h3 style="font-weight: 600; color: #0066cc; margin-bottom: 8px;">${escape_html(t("How It Works:"))}</h3> <p style="color: #0066cc;">${escape_html(t("You'll see a card with a color, shape, and number of symbols. Sort it into one of four piles by clicking a target card. The sorting rule (color, shape, or number) will change without warning. Use the feedback to discover the current rule."))}</p></div> <p style="color: #666; margin-bottom: 20px;"><strong>${escape_html(t("Current Difficulty:"))}</strong> ${escape_html(levelLabel())}</p> <button style="width: 100%; padding: 15px; background: #0066cc; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">${escape_html(t("Continue to Instructions"))}</button></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
