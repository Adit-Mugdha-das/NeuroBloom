import { _ as bind_props } from "./index2.js";
/* empty css                                              */
import { j as fallback } from "./utils2.js";
import { e as escape_html } from "./escaping.js";
function DifficultyBadge($$renderer, $$props) {
  let label;
  let difficulty = fallback($$props["difficulty"], 5);
  let domain = fallback($$props["domain"], "");
  function getDifficultyLabel(diff) {
    if (diff <= 3) return "Easy";
    if (diff <= 6) return "Medium";
    if (diff <= 8) return "Hard";
    return "Expert";
  }
  label = getDifficultyLabel(difficulty);
  $$renderer.push(`<div class="difficulty-badge svelte-1acasio">`);
  if (domain) {
    $$renderer.push("<!--[-->");
    $$renderer.push(`<span class="domain-label svelte-1acasio">${escape_html(domain)}</span> <span class="separator svelte-1acasio">•</span>`);
  } else {
    $$renderer.push("<!--[!-->");
  }
  $$renderer.push(`<!--]--> <span class="level-text svelte-1acasio">Level ${escape_html(difficulty)}</span> <span class="level-label svelte-1acasio">(${escape_html(label)})</span></div>`);
  bind_props($$props, { difficulty, domain });
}
export {
  DifficultyBadge as D
};
