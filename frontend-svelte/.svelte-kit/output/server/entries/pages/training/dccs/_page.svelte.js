import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
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
/* empty css                                                               */
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../chunks/TaskPracticeActions.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = "";
    user.subscribe((value) => {
    });
    function t(text) {
      return translateText(text, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function durationMsLabel(value) {
      const roundedValue = Number.isFinite(Number(value)) ? Math.round(Number(value)) : 0;
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `${n(roundedValue)} মি.সে.` : `${roundedValue}ms`;
    }
    function levelLabel(value = difficulty, max = 10) {
      return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `লেভেল ${n(value)} / ${n(max)}` : `Level ${value} / ${max}`;
    }
    function ruleName(rule) {
      if (rule === "color") return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "রঙ" : "COLOR";
      if (rule === "shape") return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "আকৃতি" : "SHAPE";
      if (rule === "size") return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "আকার" : "SIZE";
      if (rule === "varies") return store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "পরিবর্তিত হবে" : "VARIES";
      return t(rule || "");
    }
    function cueInstruction(rule) {
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        return `${ruleName(rule)} অনুযায়ী সাজান`;
      }
      return `Sort by ${ruleName(rule)}`;
    }
    function phaseRule(index) {
      if (index === 1) return "color";
      if (index === 2) return "shape";
      return "varies";
    }
    function ruleExample(rule) {
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        if (rule === "color") return "লাল কার্ড এক স্তূপে যাবে, নীল অন্য স্তূপে";
        if (rule === "shape") return "বৃত্ত এক স্তূপে যাবে, তারা অন্য স্তূপে";
        if (rule === "size") return "বড় কার্ড এক স্তূপে যাবে, ছোট অন্য স্তূপে";
        return "";
      }
      if (rule === "color") return "red cards go to one pile, blue to another";
      if (rule === "shape") return "circles go to one pile, stars to another";
      if (rule === "size") return "large cards go to one pile, small to another";
      return "";
    }
    function difficultyDescription() {
      const cueDuration = 0;
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        return `প্রাথমিক স্তর: রঙ ও আকৃতি অনুযায়ী সাজানো, ${durationMsLabel(cueDuration)} সংকেত`;
      }
      return `Basic: Color & Shape sorting, ${cueDuration}ms cues`;
    }
    $$renderer2.push(`<div class="dccs-container svelte-fl147w">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="page-wrapper svelte-fl147w"><div class="task-title-row svelte-fl147w"><div class="svelte-fl147w"><h1 class="svelte-fl147w">${escape_html(t("Dimensional Change Card Sort"))}</h1> <p class="task-subtitle svelte-fl147w">${escape_html(t("DCCS — Cognitive Flexibility & Rule Switching"))}</p></div> `);
          DifficultyBadge($$renderer2, { difficulty, domain: "Cognitive Flexibility" });
          $$renderer2.push(`<!----></div> <div class="card task-concept svelte-fl147w"><div class="concept-badge svelte-fl147w">${escape_html(t("Cognitive Flexibility Assessment"))}</div> <p class="concept-body svelte-fl147w">${escape_html(store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "কার্ড বাছাই করুন, নিয়ম পরিবর্তনের সাথে মানিয়ে নিন। তিনটি ধাপে রঙ ও আকৃতি অনুযায়ী সাজান — মাঝে নিয়ম পরিবর্তন হবে। এটি সেট-শিফটিং এবং ইনহিবিটরি কন্ট্রোল পরিমাপ করে।" : "Sort cards and adapt as the rule changes. Work through three phases using color and shape rules — the rule switches between phases. This measures cognitive set-shifting and inhibitory control.")}</p></div> <div class="card svelte-fl147w"><h2 class="section-title svelte-fl147w">${escape_html(t("Three-Phase Structure"))}</h2> <div class="phases-row svelte-fl147w"><div class="phase-block phase1 svelte-fl147w"><div class="phase-num svelte-fl147w">1</div> <p class="phase-label svelte-fl147w">${escape_html(t("Pre-Switch"))}</p> <p class="phase-rule svelte-fl147w">${escape_html(cueInstruction(phaseRule(1)))}</p> <p class="phase-eg svelte-fl147w">${escape_html(ruleExample(phaseRule(1)))}</p></div> <div class="phase-arrow svelte-fl147w">\\u2192</div> <div class="phase-block phase2 svelte-fl147w"><div class="phase-num svelte-fl147w">2</div> <p class="phase-label svelte-fl147w">${escape_html(t("Post-Switch"))}</p> <p class="phase-rule svelte-fl147w">${escape_html(cueInstruction(phaseRule(2)))}</p> <p class="phase-eg svelte-fl147w">${escape_html(ruleExample(phaseRule(2)))}</p></div> <div class="phase-arrow svelte-fl147w">\\u2192</div> <div class="phase-block phase3 svelte-fl147w"><div class="phase-num svelte-fl147w">3</div> <p class="phase-label svelte-fl147w">${escape_html(t("Mixed"))}</p> <p class="phase-rule svelte-fl147w">${escape_html(t("Per-trial cue"))}</p> <p class="phase-eg svelte-fl147w">${escape_html(store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? "কখনো রঙ, কখনো আকৃতি" : "Color or Shape — cue tells you")}</p></div></div></div> <div class="card svelte-fl147w"><h2 class="section-title svelte-fl147w">${escape_html(t("How It Works"))}</h2> <div class="rules-grid svelte-fl147w"><div class="rule-item svelte-fl147w"><div class="rule-num fuchsia svelte-fl147w">1</div> <div class="rule-body svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Cards Have Two Features"))}</strong> <span class="svelte-fl147w">${escape_html(t("Each card has a color (red or blue) and a shape (circle or star)"))}</span></div></div> <div class="rule-item svelte-fl147w"><div class="rule-num fuchsia svelte-fl147w">2</div> <div class="rule-body svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Click the Matching Target"))}</strong> <span class="svelte-fl147w">${escape_html(t("Two target cards are shown. Click the one that matches the rule."))}</span></div></div> <div class="rule-item svelte-fl147w"><div class="rule-num fuchsia svelte-fl147w">3</div> <div class="rule-body svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Rules Switch Between Phases"))}</strong> <span class="svelte-fl147w">${escape_html(t("Phase 1 uses one rule; Phase 2 switches to a new rule. Ignore your old response pattern."))}</span></div></div> <div class="rule-item svelte-fl147w"><div class="rule-num fuchsia svelte-fl147w">4</div> <div class="rule-body svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Watch the Cue in Phase 3"))}</strong> <span class="svelte-fl147w">${escape_html(t("In the mixed phase, a brief cue flashes before each card. It tells you which rule to use."))}</span></div></div></div></div> <div class="info-grid svelte-fl147w"><div class="card svelte-fl147w"><h3 class="card-heading svelte-fl147w">${escape_html(t("Session Details"))}</h3> <ul class="detail-list svelte-fl147w"><li class="svelte-fl147w"><span class="dl-label svelte-fl147w">${escape_html(t("Difficulty"))}</span> <span class="dl-value fuchsia-val svelte-fl147w">${escape_html(levelLabel())}</span></li> <li class="svelte-fl147w"><span class="dl-label svelte-fl147w">${escape_html(t("Total Trials"))}</span> <span class="dl-value svelte-fl147w">${escape_html(n(40))}</span></li> <li class="svelte-fl147w"><span class="dl-label svelte-fl147w">${escape_html(t("Cue Duration"))}</span> <span class="dl-value svelte-fl147w">${escape_html(durationMsLabel(0))}</span></li> <li class="svelte-fl147w"><span class="dl-label svelte-fl147w">${escape_html(t("Phases"))}</span> <span class="dl-value svelte-fl147w">${escape_html(t("3 phases"))}</span></li></ul> <p class="diff-desc svelte-fl147w">${escape_html(difficultyDescription())}</p> `);
          {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--></div> <div class="card svelte-fl147w"><h3 class="card-heading svelte-fl147w">${escape_html(t("What It Measures"))}</h3> <ul class="measure-list svelte-fl147w"><li class="svelte-fl147w"><span class="dot fuchsia svelte-fl147w"></span><div class="svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Set-Shifting"))}</strong><p class="svelte-fl147w">${escape_html(t("Switching between active sorting rules"))}</p></div></li> <li class="svelte-fl147w"><span class="dot fuchsia svelte-fl147w"></span><div class="svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Cognitive Flexibility"))}</strong><p class="svelte-fl147w">${escape_html(t("Adapting to new task demands"))}</p></div></li> <li class="svelte-fl147w"><span class="dot fuchsia svelte-fl147w"></span><div class="svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Inhibitory Control"))}</strong><p class="svelte-fl147w">${escape_html(t("Suppressing the previously rewarded response"))}</p></div></li> <li class="svelte-fl147w"><span class="dot fuchsia svelte-fl147w"></span><div class="svelte-fl147w"><strong class="svelte-fl147w">${escape_html(t("Switch Cost"))}</strong><p class="svelte-fl147w">${escape_html(t("Reaction time penalty when the rule changes"))}</p></div></li></ul></div></div> <div class="card clinical-info svelte-fl147w"><h3 class="card-heading svelte-fl147w">${escape_html(t("Clinical Significance"))}</h3> <div class="clinical-grid svelte-fl147w"><div class="clinical-item svelte-fl147w"><span class="ci-label svelte-fl147w">${escape_html(t("Validated By"))}</span> <span class="svelte-fl147w">Zelazo (2006); ${escape_html(t("developmental and clinical research"))}</span></div> <div class="clinical-item svelte-fl147w"><span class="ci-label svelte-fl147w">${escape_html(t("MS Relevance"))}</span> <span class="svelte-fl147w">${escape_html(t("Sensitive to MS-related executive and frontal lobe dysfunction"))}</span></div> <div class="clinical-item svelte-fl147w"><span class="ci-label svelte-fl147w">${escape_html(t("Key Metric"))}</span> <span class="svelte-fl147w">${escape_html(t("Switch Cost = extra reaction time when rule changes; Perseverative errors = stuck on old rule"))}</span></div> <div class="clinical-item svelte-fl147w"><span class="ci-label svelte-fl147w">${escape_html(t("Advantage"))}</span> <span class="svelte-fl147w">${escape_html(t("Simpler and less frustrating than WCST; clear rule-switching paradigm"))}</span></div></div></div> <div class="card perf-guide svelte-fl147w"><h3 class="card-heading svelte-fl147w">${escape_html(t("Performance Guide — Switch Cost"))}</h3> <div class="norm-bars svelte-fl147w"><div class="norm-bar svelte-fl147w"><span class="norm-label svelte-fl147w">${escape_html(t("Excellent"))}</span> <div class="norm-track svelte-fl147w"><div class="norm-fill fuchsia-fill svelte-fl147w" style="width:25%"></div></div> <span class="norm-val svelte-fl147w">&lt; 100ms</span></div> <div class="norm-bar svelte-fl147w"><span class="norm-label svelte-fl147w">${escape_html(t("Good"))}</span> <div class="norm-track svelte-fl147w"><div class="norm-fill fuchsia-mid svelte-fl147w" style="width:50%"></div></div> <span class="norm-val svelte-fl147w">100–200ms</span></div> <div class="norm-bar svelte-fl147w"><span class="norm-label svelte-fl147w">${escape_html(t("Developing"))}</span> <div class="norm-track svelte-fl147w"><div class="norm-fill fuchsia-low svelte-fl147w" style="width:75%"></div></div> <span class="norm-val svelte-fl147w">> 200ms</span></div></div></div> <div class="btn-row svelte-fl147w">`);
          TaskPracticeActions($$renderer2, {
            locale: store_get($$store_subs ??= {}, "$locale", locale),
            startLabel: t("Start DCCS Test"),
            statusMessage: practiceStatusMessage
          });
          $$renderer2.push(`<!----></div></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
