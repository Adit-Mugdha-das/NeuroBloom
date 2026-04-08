import { s as store_get, u as unsubscribe_stores, d as bind_props } from "./index2.js";
import { t as translateText, f as formatNumber, l as locale } from "./index3.js";
/* empty css                                              */
import { $ as fallback } from "./utils2.js";
import { e as escape_html } from "./escaping.js";
function DifficultyBadge($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let label, domainLabel, difficultyLabel, displayDifficulty;
    let difficulty = fallback($$props["difficulty"], 5);
    let domain = fallback($$props["domain"], "");
    function getDifficultyLabel(diff) {
      if (diff <= 3) return "Easy";
      if (diff <= 6) return "Medium";
      if (diff <= 8) return "Hard";
      return "Expert";
    }
    label = translateText(getDifficultyLabel(difficulty), store_get($$store_subs ??= {}, "$locale", locale));
    domainLabel = domain ? translateText(domain, store_get($$store_subs ??= {}, "$locale", locale)) : "";
    difficultyLabel = translateText("Level", store_get($$store_subs ??= {}, "$locale", locale));
    displayDifficulty = formatNumber(difficulty, store_get($$store_subs ??= {}, "$locale", locale));
    $$renderer2.push(`<div class="difficulty-badge svelte-1ty1kqj">`);
    if (domain) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="domain-label svelte-1ty1kqj">${escape_html(domainLabel)}</span> <span class="separator svelte-1ty1kqj">•</span>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <span class="level-text svelte-1ty1kqj">${escape_html(difficultyLabel)} ${escape_html(displayDifficulty)}</span> <span class="level-label svelte-1ty1kqj">(${escape_html(label)})</span></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { difficulty, domain });
  });
}
export {
  DifficultyBadge as D
};
