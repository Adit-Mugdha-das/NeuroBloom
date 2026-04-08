import { h as head, s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { t as translateText, l as locale, f as formatNumber, a as localeText } from "../../../../chunks/index3.js";
/* empty css                                                                 */
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
/* empty css                                                               */
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../chunks/TaskPracticeActions.js";
import { a as getTaskDifficultyDescription } from "../../../../chunks/task-ui.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let sessionData = null;
    TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = "";
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    function lt(englishText, banglaText) {
      return localeText({ en: englishText, bn: banglaText }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function digitsLabel(count) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(count)}টি অঙ্ক` : `${count} digits`;
    }
    function secondsLabel(value) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(value)} সেকেন্ড` : `${value} seconds`;
    }
    function intervalLabel(value) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(value)} সেকেন্ড পরপর` : `${value}s intervals`;
    }
    function actualTestButtonLabel(total) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `আসল পরীক্ষা শুরু করুন (${digitsLabel(total)})` : `Start Actual Test (${total} digits)`;
    }
    function localizedDigit(value) {
      return n(value);
    }
    function currentPaceDescription() {
      const fallbackDescription = "Standard PASAT-3";
      return getTaskDifficultyDescription("pasat", sessionData?.difficulty, store_get($$store_subs ??= {}, "$locale", locale), t(fallbackDescription));
    }
    head("1rcnj8a", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(lt("PASAT - NeuroBloom", "পাসাট - NeuroBloom"))}</title>`);
      });
    });
    $$renderer2.push(`<div class="pasat-container svelte-1rcnj8a" data-localize-skip=""><div class="pasat-inner svelte-1rcnj8a">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="instructions-card svelte-1rcnj8a"><div class="header-content svelte-1rcnj8a"><div class="title-row svelte-1rcnj8a"><h1 class="svelte-1rcnj8a">🎯 ${escape_html(t("PASAT"))}</h1> `);
          DifficultyBadge($$renderer2, {
            difficulty: 5,
            domain: "Attention"
          });
          $$renderer2.push(`<!----></div> <p class="subtitle svelte-1rcnj8a">${escape_html(t("Paced Auditory Serial Addition Test · MS Gold Standard"))}</p> <div class="gold-badge svelte-1rcnj8a">⭐⭐⭐⭐⭐ ${escape_html(t("CLINICAL GOLD STANDARD FOR MS"))}</div></div> `);
          {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--> <div class="task-concept svelte-1rcnj8a"><h3 class="svelte-1rcnj8a">🔢 ${escape_html(t("The Golden Rule"))}</h3> <p class="svelte-1rcnj8a">${escape_html(t("Add each NEW digit to the PREVIOUS digit — not to your running total. This is the key rule!"))}</p> <div class="pasat-example svelte-1rcnj8a"><div class="ex-step ex-first svelte-1rcnj8a"><div class="ex-digit svelte-1rcnj8a">${escape_html(localizedDigit(3))}</div> <div class="ex-hint svelte-1rcnj8a">${escape_html(t("Remember it"))}</div></div> <div class="ex-arrow svelte-1rcnj8a">→</div> <div class="ex-step svelte-1rcnj8a"><div class="ex-digit svelte-1rcnj8a">${escape_html(localizedDigit(5))}</div> <div class="ex-hint svelte-1rcnj8a">${escape_html(t("Answer"))}: <strong class="svelte-1rcnj8a">${escape_html(localizedDigit(8))}</strong></div> <div class="ex-sub svelte-1rcnj8a">${escape_html(localizedDigit(3))}+${escape_html(localizedDigit(5))}</div></div> <div class="ex-arrow svelte-1rcnj8a">→</div> <div class="ex-step svelte-1rcnj8a"><div class="ex-digit svelte-1rcnj8a">${escape_html(localizedDigit(2))}</div> <div class="ex-hint svelte-1rcnj8a">${escape_html(t("Answer"))}: <strong class="svelte-1rcnj8a">${escape_html(localizedDigit(7))}</strong></div> <div class="ex-sub svelte-1rcnj8a">${escape_html(localizedDigit(5))}+${escape_html(localizedDigit(2))}</div></div> <div class="ex-arrow svelte-1rcnj8a">→</div> <div class="ex-step svelte-1rcnj8a"><div class="ex-digit svelte-1rcnj8a">${escape_html(localizedDigit(9))}</div> <div class="ex-hint svelte-1rcnj8a">${escape_html(t("Answer"))}: <strong class="svelte-1rcnj8a">${escape_html(localizedDigit(11))}</strong></div> <div class="ex-sub svelte-1rcnj8a">${escape_html(localizedDigit(2))}+${escape_html(localizedDigit(9))}</div></div></div> <div class="key-rule-box svelte-1rcnj8a"><strong>⚠️ ${escape_html(t("KEY RULE:"))}</strong> ${escape_html(t("Always add to the PREVIOUS digit you saw — not your last answer!"))}</div></div> <div class="rules-grid svelte-1rcnj8a"><div class="rule-card svelte-1rcnj8a"><span class="rule-icon svelte-1rcnj8a">👁️</span> <div class="rule-text svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Step 1: See the Digit"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("A digit (1–9) appears on screen"))}</span></div></div> <div class="rule-card svelte-1rcnj8a"><span class="rule-icon svelte-1rcnj8a">➕</span> <div class="rule-text svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Step 2: Add to Previous"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("Add it to the digit you just saw (not your last answer!)"))}</span></div></div> <div class="rule-card svelte-1rcnj8a"><span class="rule-icon svelte-1rcnj8a">⌨️</span> <div class="rule-text svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Step 3: Type Your Sum"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("Enter the answer and press Enter quickly"))}</span></div></div> <div class="rule-card svelte-1rcnj8a"><span class="rule-icon svelte-1rcnj8a">⏱️</span> <div class="rule-text svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Step 4: Keep Pace"))}</strong> <span class="svelte-1rcnj8a">${escape_html(store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `প্রতি ${secondsLabel(3)} পরপর নতুন অঙ্ক আসবে` : `New digit every ${3} seconds`)}</span></div></div></div> <div class="info-grid svelte-1rcnj8a"><div class="info-section svelte-1rcnj8a"><h4 class="svelte-1rcnj8a">💡 ${escape_html(t("Tips for Success"))}</h4> <ul class="tips-list svelte-1rcnj8a"><li class="svelte-1rcnj8a"><strong>${escape_html(t("Forget your answer:"))}</strong> ${escape_html(t("only remember the digit you just saw"))}</li> <li class="svelte-1rcnj8a"><strong>${escape_html(t("Don't keep a total:"))}</strong> ${escape_html(t("that's not the task!"))}</li> <li class="svelte-1rcnj8a"><strong>${escape_html(t("If you miss one:"))}</strong> ${escape_html(t("reset with the next digit"))}</li> <li class="svelte-1rcnj8a"><strong>${escape_html(t("Stay calm:"))}</strong> ${escape_html(t("even healthy adults find this hard"))}</li></ul></div> <div class="info-section svelte-1rcnj8a"><h4 class="svelte-1rcnj8a">📋 ${escape_html(t("Test Format"))}</h4> <ul class="structure-list svelte-1rcnj8a"><li class="svelte-1rcnj8a"><span class="struct-key svelte-1rcnj8a">${escape_html(t("Digits"))}</span> <span class="struct-val svelte-1rcnj8a">${escape_html(n(60))}</span></li> <li class="svelte-1rcnj8a"><span class="struct-key svelte-1rcnj8a">${escape_html(t("Pace"))}</span> <span class="struct-val svelte-1rcnj8a">${escape_html(intervalLabel(3))}</span></li> <li class="svelte-1rcnj8a"><span class="struct-key svelte-1rcnj8a">${escape_html(t("Version"))}</span> <span class="struct-val svelte-1rcnj8a">${escape_html(currentPaceDescription())}</span></li> <li class="svelte-1rcnj8a"><span class="struct-key svelte-1rcnj8a">${escape_html(t("Input"))}</span> <span class="struct-val svelte-1rcnj8a">${escape_html(t("Keyboard / number pad"))}</span></li></ul></div></div> <div class="clinical-info svelte-1rcnj8a"><h4 class="svelte-1rcnj8a">🏥 ${escape_html(t("Clinical Significance"))}</h4> <div class="clinical-grid svelte-1rcnj8a"><div class="clinical-item svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("MS Gold Standard"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("Most widely used MS cognitive test in clinical trials"))}</span></div> <div class="clinical-item svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Sustained Attention"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("Tracks attention maintenance over the whole session"))}</span></div> <div class="clinical-item svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Lesion Correlation"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("Performance correlates with brain lesion burden"))}</span></div> <div class="clinical-item svelte-1rcnj8a"><strong class="svelte-1rcnj8a">${escape_html(t("Gronwall, 1977"))}</strong> <span class="svelte-1rcnj8a">${escape_html(t("Extensively validated in MS populations worldwide"))}</span></div></div></div> <div class="perf-guide svelte-1rcnj8a"><h4 class="svelte-1rcnj8a">📊 ${escape_html(t("Performance Reference"))}</h4> <div class="norm-bars svelte-1rcnj8a"><div class="norm-bar norm-excellent svelte-1rcnj8a"><span class="norm-label svelte-1rcnj8a">${escape_html(t("Excellent"))}</span> <span class="norm-val svelte-1rcnj8a">≥85% ${escape_html(t("accuracy"))}</span></div> <div class="norm-bar norm-good svelte-1rcnj8a"><span class="norm-label svelte-1rcnj8a">${escape_html(t("Good"))}</span> <span class="norm-val svelte-1rcnj8a">70–84%</span></div> <div class="norm-bar norm-avg svelte-1rcnj8a"><span class="norm-label svelte-1rcnj8a">${escape_html(t("Average"))}</span> <span class="norm-val svelte-1rcnj8a">55–69%</span></div> <div class="norm-bar norm-fair svelte-1rcnj8a"><span class="norm-label svelte-1rcnj8a">${escape_html(t("Fair"))}</span> <span class="norm-val svelte-1rcnj8a">40–54%</span></div> <div class="norm-bar norm-needs svelte-1rcnj8a"><span class="norm-label svelte-1rcnj8a">${escape_html(t("Developing"))}</span> <span class="norm-val svelte-1rcnj8a">&lt;40%</span></div></div> <p class="norm-note svelte-1rcnj8a">*${escape_html(t("Scores depend on pace — faster intervals = harder task"))}</p></div> <div class="button-group svelte-1rcnj8a"><button class="btn-secondary svelte-1rcnj8a">✏️ ${escape_html(t("Try Practice (4 digits)"))}</button> `);
          TaskPracticeActions($$renderer2, {
            locale: store_get($$store_subs ??= {}, "$locale", locale),
            startLabel: actualTestButtonLabel(sessionData?.total_trials),
            practiceVisible: false,
            statusMessage: practiceStatusMessage,
            align: "center"
          });
          $$renderer2.push(`<!----> <button class="help-link svelte-1rcnj8a">📖 ${escape_html(t("More Information"))}</button></div></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
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
