import { s as store_get, u as unsubscribe_stores } from "../../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import "../../../../../chunks/api.js";
import { t as translateText, l as locale, f as formatNumber, b as localizeStimulusSymbol } from "../../../../../chunks/index3.js";
import { u as user } from "../../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let nBackLevel = 1;
    let totalTrials = 20;
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function stimulus(value) {
      return localizeStimulusSymbol(value, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function nBackLabel(value = nBackLevel) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(value)}-ব্যাক` : `${value}-Back`;
    }
    function stepAgoText(value = nBackLevel) {
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        return `${n(value)} ধাপ আগে`;
      }
      return `${value} step${value > 1 ? "s" : ""} ago`;
    }
    function secondsText(value) {
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        return `${n(value)} সেকেন্ড`;
      }
      return `${value} seconds`;
    }
    $$renderer2.push(`<div class="test-container svelte-z6zxfp" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-z6zxfp"><h1 class="svelte-z6zxfp">🧠 ${escape_html(t("Working Memory Test"))}</h1> <h2 style="color: #764ba2; font-size: 1.5rem; margin-bottom: 2rem; font-weight: 600;" class="svelte-z6zxfp">${escape_html(nBackLabel())} ${escape_html(t("Task"))}</h2> <div class="instructions svelte-z6zxfp"><div class="instruction-header svelte-z6zxfp"><h3 class="svelte-z6zxfp">📋 ${escape_html(t("How It Works:"))}</h3></div> <div class="instruction-steps svelte-z6zxfp"><div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">${escape_html(n(1))}</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">${escape_html(t("You'll see letters appear one at a time on screen"))}</p></div></div> <div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">${escape_html(n(2))}</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">${escape_html(t("Each letter stays for 2 seconds"))}</p></div></div> <div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">${escape_html(n(3))}</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">`);
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`${escape_html(`বর্তমান অক্ষরটি ${stepAgoText()} আগের অক্ষরের মতো হলে `)} <strong class="match-btn svelte-z6zxfp">✓ ${escape_html(t("Match"))}</strong>  চাপুন`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Click  <strong class="match-btn svelte-z6zxfp">✓ ${escape_html(t("Match"))}</strong> ${escape_html(` if the current letter is the same as the letter from ${stepAgoText()}`)}`);
      }
      $$renderer2.push(`<!--]--></p></div></div> <div class="step svelte-z6zxfp"><div class="step-number svelte-z6zxfp">${escape_html(n(4))}</div> <div class="step-content svelte-z6zxfp"><p class="svelte-z6zxfp">`);
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`ভিন্ন হলে  <strong class="no-match-btn svelte-z6zxfp">✗ ${escape_html(t("No Match"))}</strong>  চাপুন`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`Click  <strong class="no-match-btn svelte-z6zxfp">✗ ${escape_html(t("No Match"))}</strong>  if it's different`);
      }
      $$renderer2.push(`<!--]--></p></div></div></div> <div class="example-box svelte-z6zxfp"><h4 class="svelte-z6zxfp">💡 ${escape_html(t("Example for"))} ${escape_html(nBackLabel())}:</h4> <div class="sequence-display svelte-z6zxfp"><div class="sequence-item svelte-z6zxfp"><span class="letter-demo svelte-z6zxfp">${escape_html(stimulus("A"))}</span> <span class="position svelte-z6zxfp">${escape_html(t("Position"))} ${escape_html(n(1))}</span></div> <div class="arrow svelte-z6zxfp">→</div> <div class="sequence-item svelte-z6zxfp"><span class="letter-demo svelte-z6zxfp">${escape_html(stimulus("B"))}</span> <span class="position svelte-z6zxfp">${escape_html(t("Position"))} ${escape_html(n(2))}</span></div> <div class="arrow svelte-z6zxfp">→</div> <div class="sequence-item highlight svelte-z6zxfp"><span class="letter-demo svelte-z6zxfp">${escape_html(stimulus("A"))}</span> <span class="position svelte-z6zxfp">${escape_html(t("Position"))} ${escape_html(n(3))}</span> <span class="match-indicator svelte-z6zxfp">✓ ${escape_html(t("MATCH!"))}</span></div></div> <p class="example-explanation svelte-z6zxfp">`);
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`${escape_html(`অবস্থান ${n(3)}-এ আপনি আবার `)} <strong class="svelte-z6zxfp">${escape_html(stimulus("A"))}</strong> ${escape_html(` দেখছেন। ${stepAgoText()} তাকালে আগেও `)} <strong class="svelte-z6zxfp">${escape_html(stimulus("A"))}</strong>  ছিল, তাই  <strong class="match-btn svelte-z6zxfp">${escape_html(t("Match"))}</strong>  চাপুন!`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`At position 3, you see  <strong class="svelte-z6zxfp">${escape_html(stimulus("A"))}</strong> ${escape_html(` again. Looking back ${nBackLevel} step${""}, you also saw `)} <strong class="svelte-z6zxfp">${escape_html(stimulus("A"))}</strong>  → Click  <strong class="match-btn svelte-z6zxfp">${escape_html(t("Match"))}</strong> !`);
      }
      $$renderer2.push(`<!--]--></p></div> <div class="test-info svelte-z6zxfp"><div class="info-item svelte-z6zxfp"><span class="info-label svelte-z6zxfp">${escape_html(t("Total Trials:"))}</span> <span class="info-value svelte-z6zxfp">${escape_html(n(totalTrials))} ${escape_html(t("letters"))}</span></div> <div class="info-item svelte-z6zxfp"><span class="info-label svelte-z6zxfp">${escape_html(t("Difficulty:"))}</span> <span class="info-value svelte-z6zxfp">${escape_html(nBackLabel())}</span></div> <div class="info-item svelte-z6zxfp"><span class="info-label svelte-z6zxfp">${escape_html(t("Time per Letter:"))}</span> <span class="info-value svelte-z6zxfp">${escape_html(secondsText(2))}</span></div></div></div> <div class="button-group svelte-z6zxfp"><button class="btn-primary btn-large svelte-z6zxfp">🚀 ${escape_html(t("Start Test"))}</button> <button class="btn-secondary svelte-z6zxfp">← ${escape_html(t("Back to Dashboard"))}</button></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
