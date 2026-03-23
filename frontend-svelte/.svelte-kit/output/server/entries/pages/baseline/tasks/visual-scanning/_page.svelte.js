import { h as head, u as unsubscribe_stores, s as store_get } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import { o as onDestroy } from "../../../../../chunks/index-server.js";
import { t as translateText, l as locale, a as localeText, f as formatNumber } from "../../../../../chunks/index3.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
import { h as html } from "../../../../../chunks/html.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let totalTargets = 5;
    const LETTER_SETS = {
      en: {
        target: "T",
        distractors: ["L", "I", "F", "E", "P"],
        distractorPreview: "L I F E P"
      },
      bn: {
        target: "ট",
        distractors: ["ড", "ঠ", "ণ", "ল", "ফ"],
        distractorPreview: "ড ঠ ণ ল ফ"
      }
    };
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function activeLetterSet() {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? LETTER_SETS.bn : LETTER_SETS.en;
    }
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    onDestroy(() => {
    });
    head("29xk7i", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(lt("Visual Scanning Test - NeuroBloom", "ভিজ্যুয়াল স্ক্যানিং টেস্ট - NeuroBloom"))}</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-29xk7i" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-29xk7i"><h1 class="svelte-29xk7i">${escape_html(t("Visual Scanning Test"))}</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-29xk7i">${escape_html(t("Visual Search Task"))}</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-29xk7i"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-29xk7i">${escape_html(t("Instructions:"))}</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-29xk7i"><li class="svelte-29xk7i">${escape_html(lt(`You'll see a grid of letters (${activeLetterSet().distractorPreview}, ${activeLetterSet().target})`, `আপনি অক্ষরের একটি গ্রিড দেখবেন (${activeLetterSet().distractorPreview}, ${activeLetterSet().target})`))}</li> <li class="svelte-29xk7i">${escape_html(lt(`Find and click ALL the letter "${activeLetterSet().target}"`, `সব "${activeLetterSet().target}" অক্ষর খুঁজে ক্লিক করুন`))}</li> <li class="svelte-29xk7i">${html(lt(`There are <strong>${totalTargets} targets</strong> hidden in the grid`, `গ্রিডে <strong>${n(totalTargets)}টি লক্ষ্য</strong> লুকানো আছে`))}</li> <li class="svelte-29xk7i">${escape_html(t("Work as quickly and accurately as possible"))}</li> <li class="svelte-29xk7i">${escape_html(t("Timer starts when the grid appears"))}</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-29xk7i"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-29xk7i">${escape_html(t("What to Look For:"))}</h4> <div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px;" class="svelte-29xk7i"><div class="svelte-29xk7i"><p style="color: #4caf50; font-size: 48px; font-weight: bold; margin: 0;" class="svelte-29xk7i">${escape_html(activeLetterSet().target)}</p> <p style="color: #666; font-size: 14px;" class="svelte-29xk7i">${escape_html(t("FIND THIS"))}</p></div> <div class="svelte-29xk7i"><p style="color: #999; font-size: 48px; font-weight: bold; margin: 0;" class="svelte-29xk7i">${escape_html(activeLetterSet().distractorPreview)}</p> <p style="color: #666; font-size: 14px;" class="svelte-29xk7i">${escape_html(t("IGNORE THESE"))}</p></div></div></div></div> <button class="btn-primary svelte-29xk7i" style="margin-top: 40px;">${escape_html(t("Start Test"))}</button> <button class="btn-secondary svelte-29xk7i">${escape_html(t("Back to Dashboard"))}</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
