import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
/* empty css                                                               */
import "../../../../chunks/api.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { T as TaskPracticeActions } from "../../../../chunks/TaskPracticeActions.js";
import { a as localeText, l as locale } from "../../../../chunks/index3.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    let earnedBadges = [];
    TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = "";
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="ufov-container svelte-9pq8xw"><div class="task-header svelte-9pq8xw"><button class="back-btn svelte-9pq8xw">Back to Dashboard</button> <div class="header-center svelte-9pq8xw"><h1 class="task-title svelte-9pq8xw">Useful Field of View</h1> `);
    DifficultyBadge($$renderer2, { difficulty, domain: "Visual Scanning" });
    $$renderer2.push(`<!----></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="page-content svelte-9pq8xw"><div class="concept-card svelte-9pq8xw"><div class="concept-badge svelte-9pq8xw">Visual Scanning · Divided Attention</div> <h2 class="svelte-9pq8xw">Useful Field of View (UFOV)</h2> <p class="svelte-9pq8xw">Images flash at the center and periphery of your visual field for extremely brief durations — as short as 17ms at the highest level. Your task is to identify the central vehicle and locate peripheral shapes before the display disappears. This tests how quickly and broadly you can process visual information in a single glance.</p></div> <div class="rules-card svelte-9pq8xw"><h3 class="svelte-9pq8xw">How It Works</h3> <ol class="rules-list svelte-9pq8xw"><li class="svelte-9pq8xw"><strong class="svelte-9pq8xw">Fix your gaze on the center cross (+)</strong> — keep your eyes perfectly still during the flash.</li> <li class="svelte-9pq8xw"><strong class="svelte-9pq8xw">A brief stimulus appears</strong> — a vehicle at center and possibly a shape in the periphery. Duration ranges from 500ms (Level 1) down to 17ms (Level 10).</li> <li class="svelte-9pq8xw"><strong class="svelte-9pq8xw">Respond immediately</strong> — report the central vehicle type (car or truck), and for harder subtests, the position of the peripheral shape.</li></ol></div> <div class="info-grid svelte-9pq8xw"><div class="info-card svelte-9pq8xw"><div class="info-label svelte-9pq8xw">Subtest 1</div> <div class="info-title svelte-9pq8xw">Central Only</div> <p class="svelte-9pq8xw">Identify the vehicle in the center of the display. Measures pure visual processing speed with no distractions.</p></div> <div class="info-card svelte-9pq8xw"><div class="info-label svelte-9pq8xw">Subtest 2</div> <div class="info-title svelte-9pq8xw">Central + Peripheral</div> <p class="svelte-9pq8xw">Identify the center vehicle and locate the peripheral shape simultaneously. Measures divided visual attention.</p></div> <div class="info-card svelte-9pq8xw"><div class="info-label svelte-9pq8xw">Subtest 3</div> <div class="info-title svelte-9pq8xw">With Distractors</div> <p class="svelte-9pq8xw">Same as Subtest 2 but with surrounding visual noise. Measures selective visual attention under clutter.</p></div></div> <div class="tip-card svelte-9pq8xw"><div class="tip-title svelte-9pq8xw">Strategy</div> <p class="svelte-9pq8xw">Do not try to consciously analyze — respond with your immediate impression. At higher levels the flash is too brief for deliberation. Trust what you sensed, even if uncertain, and answer as quickly as possible.</p> <div class="timing-scale svelte-9pq8xw"><span class="ts-start svelte-9pq8xw">Level 1 · 500ms</span> <div class="ts-bar svelte-9pq8xw"></div> <span class="ts-end svelte-9pq8xw">Level 10 · 17ms</span></div></div> <div class="clinical-card svelte-9pq8xw"><h3 class="svelte-9pq8xw">Clinical Basis</h3> <p class="svelte-9pq8xw">Ball et al. (1993) demonstrated that UFOV reduction is the strongest predictor of at-fault driving crashes, outperforming visual acuity, reaction time, and cognitive test scores. In multiple sclerosis, UFOV impairment correlates with white matter lesion volume and predicts difficulty with driving and other complex real-world tasks. It is a key measure of visual processing speed and divided attention in MS rehabilitation programmes.</p></div> `);
        TaskPracticeActions($$renderer2, {
          locale: store_get($$store_subs ??= {}, "$locale", locale),
          startLabel: localeText({ en: "Start Task", bn: "টাস্ক শুরু করুন" }, store_get($$store_subs ??= {}, "$locale", locale)),
          statusMessage: practiceStatusMessage,
          align: "center"
        });
        $$renderer2.push(`<!----></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--> `);
    if (earnedBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: earnedBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
