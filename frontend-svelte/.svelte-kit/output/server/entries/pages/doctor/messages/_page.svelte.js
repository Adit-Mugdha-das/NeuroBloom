import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DoctorWorkspaceShell } from "../../../../chunks/DoctorWorkspaceShell.js";
import "../../../../chunks/api.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let unreadCount = 0;
    user.subscribe((value) => {
    });
    DoctorWorkspaceShell($$renderer2, {
      title: "Messages",
      subtitle: "Patient conversations in a calmer clinical workspace, with the conversation list and thread separated clearly.",
      maxWidth: "1360px",
      children: ($$renderer3) => {
        $$renderer3.push(`<section class="messaging-shell svelte-1w1xh6n"><aside class="conversation-list svelte-1w1xh6n"><div class="panel-head svelte-1w1xh6n"><p class="panel-kicker svelte-1w1xh6n">Inbox</p> <h2 class="svelte-1w1xh6n">Patient Conversations</h2></div> `);
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<p class="state-copy svelte-1w1xh6n">Loading messages...</p>`);
        }
        $$renderer3.push(`<!--]--></aside> <section class="conversation-panel svelte-1w1xh6n">`);
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<div class="empty-thread svelte-1w1xh6n"><h2 class="svelte-1w1xh6n">Select a patient</h2> <p class="svelte-1w1xh6n">Open a conversation from the left panel to review history and send a message.</p></div>`);
        }
        $$renderer3.push(`<!--]--></section></section>`);
      },
      $$slots: {
        default: true,
        actions: ($$renderer3) => {
          {
            $$renderer3.push(`<div class="message-pill svelte-1w1xh6n">Unread ${escape_html(unreadCount)}</div>`);
          }
        }
      }
    });
  });
}
export {
  _page as default
};
