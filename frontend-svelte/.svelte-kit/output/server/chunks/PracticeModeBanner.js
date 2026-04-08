import { d as bind_props } from "./index2.js";
import { g as getPracticeCopy } from "./TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { $ as fallback } from "./utils2.js";
import { e as escape_html } from "./escaping.js";
function PracticeModeBanner($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let practiceCopy;
    let locale = fallback($$props["locale"], "en");
    practiceCopy = getPracticeCopy(locale);
    $$renderer2.push(`<div class="practice-banner svelte-189zwpb" role="status" aria-live="polite"><div class="badge svelte-189zwpb">?</div> <div class="copy"><div class="title svelte-189zwpb">${escape_html(practiceCopy.bannerTitle)}</div> <div class="text svelte-189zwpb">${escape_html(practiceCopy.bannerText)}</div></div></div>`);
    bind_props($$props, { locale });
  });
}
export {
  PracticeModeBanner as P
};
