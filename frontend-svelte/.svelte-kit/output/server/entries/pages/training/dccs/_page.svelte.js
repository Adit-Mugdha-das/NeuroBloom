import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { t as translateText, l as locale, f as formatNumber } from "../../../../chunks/index3.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    let newBadges = [];
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
        return `${ruleName(rule)} অনুযায়ী সাজান`;
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
        if (rule === "size") return "বড় কার্ড এক স্তূপে যাবে, ছোট অন্য স্তূপে";
        return "";
      }
      if (rule === "color") return "red cards go to one pile, blue to another";
      if (rule === "shape") return "circles go to one pile, stars to another";
      if (rule === "size") return "large cards go to one pile, small to another";
      return "";
    }
    function phaseOverview(index) {
      const rule = phaseRule(index);
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        return `${cueInstruction(rule)} (${ruleExample(rule)})`;
      }
      return `${cueInstruction(rule)} (e.g., ${ruleExample(rule)})`;
    }
    function difficultyDescription() {
      const cueDuration = 0;
      if (store_get($$store_subs ??= {}, "$locale", locale) === "bn") {
        {
          return `প্রাথমিক স্তর: রঙ ও আকৃতি অনুযায়ী সাজানো, ${durationMsLabel(cueDuration)} সংকেত`;
        }
      }
      {
        return `Basic: Color & Shape sorting, ${cueDuration}ms cues`;
      }
    }
    $$renderer2.push(`<div style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;" class="svelte-yzdviz"><div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 1000px;" class="svelte-yzdviz"><div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;" class="svelte-yzdviz"><h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;" class="svelte-yzdviz">${escape_html(t("Dimensional Change Card Sort (DCCS)"))}</h1> `);
    DifficultyBadge($$renderer2, { difficulty: 5, domain: "Cognitive Flexibility" });
    $$renderer2.push(`<!----></div> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="svelte-yzdviz"><h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;" class="svelte-yzdviz">${escape_html(t("Cognitive Flexibility Assessment"))}</h2> <p style="font-size: 16px; color: #555; margin-bottom: 15px;" class="svelte-yzdviz">${escape_html(t("The Dimensional Change Card Sort (DCCS) measures your ability to:"))}</p> <ul style="margin-left: 30px; margin-bottom: 20px; color: #555;" class="svelte-yzdviz"><li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Switch between different sorting rules"))}</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Adapt to changing task demands"))}</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Maintain focus during rule changes"))}</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Inhibit previous responses"))}</li></ul> <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;" class="svelte-yzdviz"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;" class="svelte-yzdviz">${escape_html(t("How It Works"))}</h3> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-yzdviz"><strong class="svelte-yzdviz">${escape_html(t("Phase"))} ${escape_html(n(1))}:</strong> ${escape_html(phaseOverview(1))}</p> <p style="font-size: 14px; color: #555; margin-bottom: 8px;" class="svelte-yzdviz"><strong class="svelte-yzdviz">${escape_html(t("Phase"))} ${escape_html(n(2))}:</strong> ${escape_html(phaseOverview(2))}</p> <p style="font-size: 14px; color: #555;" class="svelte-yzdviz"><strong class="svelte-yzdviz">${escape_html(t("Phase"))} ${escape_html(n(3))}:</strong> ${escape_html(store_get($$store_subs ??= {}, "$locale", locale) === "bn" ? `মিশ্র বাছাই - প্রতিটি ট্রায়ালে সংকেত বলে দেবে ${ruleName(phaseRule(1))} নাকি ${ruleName(phaseRule(2))} অনুযায়ী সাজাতে হবে` : `Mixed sorting - a cue will tell you whether to sort by ${ruleName(phaseRule(1)).toLowerCase()} or ${ruleName(phaseRule(2)).toLowerCase()}`)}</p></div> <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;" class="svelte-yzdviz"><h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;" class="svelte-yzdviz">${escape_html(t("Instructions"))}</h3> <ul style="margin-left: 20px; color: #555;" class="svelte-yzdviz"><li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Click on the target card that matches the test card"))}</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("In Phase 3, pay attention to the cue shown before each card"))}</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Work as quickly and accurately as possible"))}</li> <li style="margin-bottom: 8px;" class="svelte-yzdviz">${escape_html(t("Total Trials:"))} ${escape_html(n(40))}</li></ul></div> <div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;" class="svelte-yzdviz"><p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;" class="svelte-yzdviz"><strong class="svelte-yzdviz">${escape_html(t("Current Difficulty:"))}</strong> ${escape_html(levelLabel())}</p> <p style="font-size: 13px; color: #0369a1;" class="svelte-yzdviz">${escape_html(difficultyDescription())}</p> `);
          {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--></div> <button style="padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" class="svelte-yzdviz">${escape_html(t("Start Test"))}</button></div>`);
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
