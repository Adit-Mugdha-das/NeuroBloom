import { h as head, u as unsubscribe_stores, s as store_get } from "../../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/state.svelte.js";
import { t as translateText, l as locale, a as localeText, f as formatNumber } from "../../../../../chunks/index3.js";
import "../../../../../chunks/api.js";
import { h as html } from "../../../../../chunks/html.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let simpleTrials;
    let choiceTrials;
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    function shapeLabel(shape) {
      const labels = {
        circle: t("Circle"),
        square: t("Square"),
        triangle: t("Triangle"),
        diamond: t("Diamond")
      };
      return labels[shape] || shape;
    }
    head("156cj0d", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(lt("Processing Speed Test - NeuroBloom", "প্রসেসিং স্পিড টেস্ট - NeuroBloom"))}</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-156cj0d" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-156cj0d"><h1 class="svelte-156cj0d">${escape_html(t("Processing Speed Test"))}</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-156cj0d">${escape_html(t("Reaction Time Assessment"))}</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-156cj0d"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-156cj0d">${escape_html(t("Two-Part Test:"))}</h3> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin: 15px 0;" class="svelte-156cj0d"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-156cj0d">${escape_html(t("Part 1: Simple Reaction Time"))}</h4> <ul style="line-height: 1.8; color: #666;" class="svelte-156cj0d"><li class="svelte-156cj0d">${html(lt('Screen will turn <strong style="color: #4caf50;">GREEN</strong>', 'স্ক্রিন <strong style="color: #4caf50;">সবুজ</strong> হবে'))}</li> <li class="svelte-156cj0d">${escape_html(t("Click as fast as possible when it turns green"))}</li> <li class="svelte-156cj0d">${escape_html(t("Don't click before it turns green!"))}</li> <li class="svelte-156cj0d">${escape_html(lt(`${n(simpleTrials)} trials`, `${n(simpleTrials)}টি ট্রায়াল`))}</li></ul></div> <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 15px 0;" class="svelte-156cj0d"><h4 style="color: #ff9800; margin-bottom: 10px;" class="svelte-156cj0d">${escape_html(t("Part 2: Choice Reaction Time"))}</h4> <ul style="line-height: 1.8; color: #666;" class="svelte-156cj0d">`);
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<li class="svelte-156cj0d">${html(lt(`You'll see <strong>${shapeLabel("circle")} ⭕</strong>, <strong>${shapeLabel("square")} ⬜</strong>, <strong>${shapeLabel("triangle")} 🔺</strong>, or <strong>${shapeLabel("diamond")} 🔶</strong>`, `আপনি দেখবেন <strong>${shapeLabel("circle")} ⭕</strong>, <strong>${shapeLabel("square")} ⬜</strong>, <strong>${shapeLabel("triangle")} 🔺</strong>, অথবা <strong>${shapeLabel("diamond")} 🔶</strong>`))}</li>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]--> <li class="svelte-156cj0d">${escape_html(t("Click the matching button as fast as possible"))}</li> <li class="svelte-156cj0d">${escape_html(t("Fast AND accurate!"))}</li> <li class="svelte-156cj0d">${escape_html(lt(`${n(choiceTrials)} trials`, `${n(choiceTrials)}টি ট্রায়াল`))}</li></ul></div></div> <button class="btn-primary svelte-156cj0d" style="margin-top: 40px;">${escape_html(t("Start Test"))}</button> <button class="btn-secondary svelte-156cj0d">${escape_html(t("Back to Dashboard"))}</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
