import { h as head, s as store_get, u as unsubscribe_stores } from "../../../../../chunks/index2.js";
import { g as goto } from "../../../../../chunks/client.js";
import { a as localeText, t as translateText, l as locale, f as formatNumber } from "../../../../../chunks/index3.js";
import "../../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../../chunks/TaskPracticeActions.js";
import "../../../../../chunks/api.js";
import { u as user } from "../../../../../chunks/stores2.js";
import { e as escape_html } from "../../../../../chunks/escaping.js";
import { h as html } from "../../../../../chunks/html.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let optimalMoves = 7;
    let practiceStatusMessage = "";
    function t(text) {
      return translateText(text ?? "", store_get($$store_subs ??= {}, "$locale", locale));
    }
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function n(value, options = {}) {
      return formatNumber(value, store_get($$store_subs ??= {}, "$locale", locale), options);
    }
    user.subscribe((value) => {
      if (!value) {
        goto();
      }
    });
    head("egb30e", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(lt("Planning Test - NeuroBloom", "পরিকল্পনা পরীক্ষা - NeuroBloom"))}</title>`);
      });
    });
    $$renderer2.push(`<div class="test-container svelte-egb30e" data-localize-skip="">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="test-card svelte-egb30e"><h1 class="svelte-egb30e">${escape_html(t("Planning Test"))}</h1> <h2 style="color: #666; font-size: 20px; margin-bottom: 30px;" class="svelte-egb30e">${escape_html(t("Tower of Hanoi"))}</h2> <div style="text-align: left; max-width: 600px; margin: 0 auto;" class="svelte-egb30e"><h3 style="color: #667eea; margin-bottom: 15px;" class="svelte-egb30e">${escape_html(t("Instructions:"))}</h3> <ul style="line-height: 1.8; color: #666;" class="svelte-egb30e"><li class="svelte-egb30e">${escape_html(t("Move all disks from the first tower to the third tower"))}</li> <li class="svelte-egb30e">${escape_html(t("You can only move one disk at a time"))}</li> <li class="svelte-egb30e">${escape_html(t("A larger disk cannot be placed on a smaller disk"))}</li> <li class="svelte-egb30e">${html(lt(`Try to complete in <strong>minimum moves (${optimalMoves})</strong>`, `যত কম সম্ভব মুভে শেষ করার চেষ্টা করুন <strong>(${n(optimalMoves)})</strong>`))}</li> <li class="svelte-egb30e">${escape_html(t("Think before you move - planning is key!"))}</li></ul> <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;" class="svelte-egb30e"><h4 style="color: #667eea; margin-bottom: 10px;" class="svelte-egb30e">${escape_html(t("How to Play:"))}</h4> <p style="color: #666; line-height: 1.6;" class="svelte-egb30e">${escape_html(lt("1. Click on a tower to pick up the top disk", "১. উপরের ডিস্ক তুলতে একটি টাওয়ারে চাপুন"))}<br class="svelte-egb30e"/> ${escape_html(lt("2. Click on another tower to place it", "২. বসাতে অন্য টাওয়ারে চাপুন"))}<br class="svelte-egb30e"/> ${escape_html(lt("3. Goal: Get all disks on the rightmost tower", "৩. লক্ষ্য: সব ডিস্ক ডানদিকের টাওয়ারে নিয়ে যান"))}</p></div></div> `);
      TaskPracticeActions($$renderer2, {
        locale: store_get($$store_subs ??= {}, "$locale", locale),
        startLabel: localeText({ en: "Start Actual Task", bn: "আসল টাস্ক শুরু করুন" }, store_get($$store_subs ??= {}, "$locale", locale)),
        statusMessage: practiceStatusMessage,
        align: "center"
      });
      $$renderer2.push(`<!----> <button class="btn-secondary svelte-egb30e">${escape_html(t("Back to Dashboard"))}</button></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
