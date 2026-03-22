import { h as head, s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { t as translateText, l as locale, f as formatNumber } from "../../../../chunks/index3.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function secondsLabel(value) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(value)} সেকেন্ড` : `${value} seconds`;
    }
    function localizedDigit(value) {
      return n(value);
    }
    head("1jl478t", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>PASAT - NeuroBloom</title>`);
      });
    });
    $$renderer2.push(`<div class="task-container svelte-1jl478t" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="instructions-panel svelte-1jl478t"><div class="task-header svelte-1jl478t"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;"><h1 class="svelte-1jl478t">🎯 ${escape_html(t("PASAT (Paced Auditory Serial Addition Test)"))}</h1> `);
          DifficultyBadge($$renderer2, {
            difficulty: 5,
            domain: "Processing Speed"
          });
          $$renderer2.push(`<!----></div> <p class="task-subtitle svelte-1jl478t">${escape_html(t("MS Gold Standard Attention Assessment"))}</p> <div class="gold-standard-badge svelte-1jl478t">⭐⭐⭐⭐⭐ ${escape_html(t("CLINICAL GOLD STANDARD"))}</div></div> <div class="clinical-context svelte-1jl478t"><h3 class="svelte-1jl478t">📋 ${escape_html(t("About This Task"))}</h3> <p>${escape_html(t("PASAT is the most widely used cognitive test in MS research and clinical trials. It measures sustained attention, working memory, and processing speed under time pressure."))}</p> <div class="ms-benefits svelte-1jl478t"><h4 class="svelte-1jl478t">✨ ${escape_html(t("Why PASAT is Critical for MS"))}</h4> <ul class="svelte-1jl478t"><li class="svelte-1jl478t"><strong>${escape_html(t("Historical Standard:"))}</strong> ${escape_html(t("Used in MS trials for decades"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("Sustained Attention:"))}</strong> ${escape_html(t("Tracks attention over extended periods"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("Lesion Correlation:"))}</strong> ${escape_html(t("Performance correlates with brain lesion burden"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("Functional Predictor:"))}</strong> ${escape_html(t("Relates to real-world cognitive abilities"))}</li></ul></div> <div class="research-note svelte-1jl478t"><strong>${escape_html(t("Research Foundation:"))}</strong> ${escape_html(t("Gronwall, 1977 - Paced Auditory Serial-Addition Task. Extensively validated in MS populations worldwide."))}</div></div> <div class="how-it-works svelte-1jl478t"><h3 class="svelte-1jl478t">🎯 ${escape_html(t("How It Works"))}</h3> <div class="pasat-example svelte-1jl478t"><div class="example-header svelte-1jl478t">${escape_html(t("Example:"))}</div> <div class="example-sequence svelte-1jl478t"><div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">${escape_html(localizedDigit(3))}</div> <div class="action svelte-1jl478t">(${escape_html(t("Remember this"))})</div></div> <div class="arrow svelte-1jl478t">→</div> <div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">${escape_html(localizedDigit(5))}</div> <div class="action svelte-1jl478t">${escape_html(t("Answer:"))} <strong>${escape_html(localizedDigit(8))}</strong></div> <div class="explanation svelte-1jl478t">(${escape_html(localizedDigit(3))} + ${escape_html(localizedDigit(5))} = ${escape_html(localizedDigit(8))})</div></div> <div class="arrow svelte-1jl478t">→</div> <div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">${escape_html(localizedDigit(2))}</div> <div class="action svelte-1jl478t">${escape_html(t("Answer:"))} <strong>${escape_html(localizedDigit(7))}</strong></div> <div class="explanation svelte-1jl478t">(${escape_html(localizedDigit(5))} + ${escape_html(localizedDigit(2))} = ${escape_html(localizedDigit(7))})</div></div> <div class="arrow svelte-1jl478t">→</div> <div class="example-step svelte-1jl478t"><div class="digit-display svelte-1jl478t">${escape_html(localizedDigit(9))}</div> <div class="action svelte-1jl478t">${escape_html(t("Answer:"))} <strong>${escape_html(localizedDigit(11))}</strong></div> <div class="explanation svelte-1jl478t">(${escape_html(localizedDigit(2))} + ${escape_html(localizedDigit(9))} = ${escape_html(localizedDigit(11))})</div></div></div></div> <div class="key-rule svelte-1jl478t"><strong>⚠️ ${escape_html(t("KEY RULE:"))}</strong> ${escape_html(t("Add each NEW digit to the PREVIOUS digit. Ignore the running total!"))}</div> <div class="instruction-steps svelte-1jl478t"><div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">${escape_html(n(1))}</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">${escape_html(t("See the Digit"))}</h4> <p class="svelte-1jl478t">${escape_html(t("A single digit (1-9) appears on screen"))}</p></div></div> <div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">${escape_html(n(2))}</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">${escape_html(t("Add to Previous"))}</h4> <p class="svelte-1jl478t">${escape_html(t("Add this digit to the one you just saw (not the answer you gave!)"))}</p></div></div> <div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">${escape_html(n(3))}</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">${escape_html(t("Type Your Answer"))}</h4> <p class="svelte-1jl478t">${escape_html(t("Enter the sum and press Enter before the next digit appears"))}</p></div></div> <div class="step svelte-1jl478t"><span class="step-number svelte-1jl478t">${escape_html(n(4))}</span> <div class="step-content svelte-1jl478t"><h4 class="svelte-1jl478t">${escape_html(t("Maintain Pace"))}</h4> <p class="svelte-1jl478t">${escape_html(store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `চালিয়ে যান! প্রতি ${secondsLabel(3)} পরপর নতুন অঙ্ক দেখাবে।` : `Keep going! Digits appear every ${3} seconds`)}</p></div></div></div></div> <div class="instruction-tips svelte-1jl478t"><h3 class="svelte-1jl478t">💡 ${escape_html(t("Tips for Success"))}</h3> <ul class="svelte-1jl478t"><li class="svelte-1jl478t"><strong>${escape_html(t("Focus on the previous digit"))}</strong> - ${escape_html(t("not your last answer"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("Don't try to keep a running total"))}</strong> - ${escape_html(t("that's not the task"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("Speed matters"))}</strong> - ${escape_html(t("try to answer before the next digit"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("If you miss one, keep going"))}</strong> - ${escape_html(t("don't get discouraged"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("Stay calm"))}</strong> - ${escape_html(t("this is challenging even for healthy adults"))}</li> <li class="svelte-1jl478t"><strong>${escape_html(t("It's okay to skip"))}</strong> - ${escape_html(t("better to wait for the next digit than lose track"))}</li></ul></div> <div class="difficulty-info svelte-1jl478t"><h4 class="svelte-1jl478t">📊 ${escape_html(t("Your Current Pace"))}</h4> <p><strong>${escape_html(secondsLabel(3))}</strong> ${escape_html(t("between digits"))}</p> <p class="difficulty-description svelte-1jl478t">${escape_html(t("Standard PASAT-3"))}</p></div> <div class="action-buttons svelte-1jl478t"><button class="primary-btn svelte-1jl478t">${escape_html(t("Start Practice (4 digits)"))}</button> <button class="help-btn svelte-1jl478t">📖 ${escape_html(t("More Information"))}</button></div></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
