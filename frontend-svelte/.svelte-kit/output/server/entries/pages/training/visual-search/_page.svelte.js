import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import "../../../../chunks/index3.js";
/* empty css                                                                 */
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let difficulty = 5;
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="container svelte-aajfcf"><div class="header svelte-aajfcf"><div class="task-badge svelte-aajfcf"><span class="domain-label svelte-aajfcf">Visual Scanning</span> <span class="difficulty-badge svelte-aajfcf">Level ${escape_html(difficulty)}</span></div> <h1 class="svelte-aajfcf">Visual Search Task</h1> <p class="subtitle svelte-aajfcf">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="search-type feature svelte-aajfcf">Feature Search</span> — Target differs by one attribute`);
    }
    $$renderer2.push(`<!--]--></p></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-aajfcf"><p class="svelte-aajfcf">Loading task...</p></div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
