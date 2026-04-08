import { a as attr_class, d as bind_props, c as stringify } from "./index2.js";
import { $ as fallback } from "./utils2.js";
import { g as getPracticeCopy } from "./TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { e as escape_html } from "./escaping.js";
import { a as attr } from "./attributes.js";
function TaskPracticeActions($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let practiceCopy;
    let locale = fallback($$props["locale"], "en");
    let startLabel = fallback($$props["startLabel"], "Start Task");
    let disabled = fallback($$props["disabled"], false);
    let practiceVisible = fallback($$props["practiceVisible"], true);
    let statusMessage = fallback($$props["statusMessage"], "");
    let align = fallback($$props["align"], "stretch");
    practiceCopy = getPracticeCopy(locale);
    $$renderer2.push(`<div${attr_class(`practice-actions ${stringify(align === "center" ? "align-center" : "")}`, "svelte-1mrgcc0")}>`);
    if (statusMessage) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="status-message svelte-1mrgcc0">${escape_html(statusMessage)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="button-row svelte-1mrgcc0"><button class="start-button svelte-1mrgcc0"${attr("disabled", disabled, true)}>${escape_html(startLabel)}</button> `);
    if (practiceVisible) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="practice-button svelte-1mrgcc0"${attr("disabled", disabled, true)}>? ${escape_html(practiceCopy.trigger)}</button>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> `);
    if (practiceVisible) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<p class="practice-helper svelte-1mrgcc0">${escape_html(practiceCopy.helper)}</p>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, {
      locale,
      startLabel,
      disabled,
      practiceVisible,
      statusMessage,
      align
    });
  });
}
export {
  TaskPracticeActions as T
};
