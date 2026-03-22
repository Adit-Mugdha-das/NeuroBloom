import { a as attr_class, e as ensure_array_like, f as bind_props, c as stringify } from "./index2.js";
import { j as fallback } from "./utils3.js";
function LoadingSkeleton($$renderer, $$props) {
  let variant = fallback(
    $$props["variant"],
    "default"
    // default, card, list
  );
  let count = fallback($$props["count"], 1);
  $$renderer.push(`<div${attr_class(`skeleton-container ${stringify(variant)}`, "svelte-1bn1hqj")}><!--[-->`);
  const each_array = ensure_array_like(Array(count));
  for (let i = 0, $$length = each_array.length; i < $$length; i++) {
    each_array[i];
    if (variant === "card") {
      $$renderer.push("<!--[-->");
      $$renderer.push(`<div class="skeleton-card svelte-1bn1hqj"><div class="skeleton skeleton-circle svelte-1bn1hqj"></div> <div class="skeleton skeleton-text svelte-1bn1hqj"></div> <div class="skeleton skeleton-text short svelte-1bn1hqj"></div></div>`);
    } else {
      $$renderer.push("<!--[!-->");
      if (variant === "list") {
        $$renderer.push("<!--[-->");
        $$renderer.push(`<div class="skeleton-list-item svelte-1bn1hqj"><div class="skeleton skeleton-avatar svelte-1bn1hqj"></div> <div class="skeleton-content svelte-1bn1hqj"><div class="skeleton skeleton-text svelte-1bn1hqj"></div> <div class="skeleton skeleton-text short svelte-1bn1hqj"></div></div></div>`);
      } else {
        $$renderer.push("<!--[!-->");
        $$renderer.push(`<div class="skeleton skeleton-block svelte-1bn1hqj"></div>`);
      }
      $$renderer.push(`<!--]-->`);
    }
    $$renderer.push(`<!--]-->`);
  }
  $$renderer.push(`<!--]--></div>`);
  bind_props($$props, { variant, count });
}
export {
  LoadingSkeleton as L
};
