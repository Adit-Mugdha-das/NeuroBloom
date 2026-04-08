import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { l as locale } from "../../../../chunks/index3.js";
/* empty css                                                                 */
/* empty css                                                               */
import { T as TaskPracticeActions } from "../../../../chunks/TaskPracticeActions.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = "";
    user.subscribe((value) => {
    });
    $$renderer2.push(`<div class="it-container svelte-1avee4x" data-localize-skip=""><div class="it-inner svelte-1avee4x">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="instructions-card svelte-1avee4x"><div class="header-content svelte-1avee4x"><div class="title-row svelte-1avee4x"><h1 class="svelte-1avee4x">⚡ Inspection Time</h1> `);
          DifficultyBadge($$renderer2, {
            difficulty: 5,
            domain: "Processing Speed"
          });
          $$renderer2.push(`<!----></div> <p class="subtitle svelte-1avee4x">How fast can your brain perceive a brief visual flash?</p> <div class="classic-badge svelte-1avee4x">Inspection Time · Vickers &amp; Smith (1986) · Pure Perceptual Speed</div></div> `);
          {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--> <div class="task-concept svelte-1avee4x"><h3 class="svelte-1avee4x">⚡ The Challenge</h3> <p class="svelte-1avee4x">Two vertical lines flash on screen for a <strong class="svelte-1avee4x">fraction of a second</strong> — then a mask covers them. Your job: say which line was <strong class="svelte-1avee4x">longer</strong> (left or right). No motor tricks — pure perception.</p> <div class="demo-lines svelte-1avee4x"><div class="demo-line-col svelte-1avee4x"><div class="demo-line svelte-1avee4x" style="height: 64px;"></div> <span class="demo-line-label svelte-1avee4x">LEFT</span></div> <div class="demo-vs svelte-1avee4x">vs</div> <div class="demo-line-col svelte-1avee4x"><div class="demo-line svelte-1avee4x" style="height: 48px;"></div> <span class="demo-line-label svelte-1avee4x">RIGHT</span></div></div> <div class="demo-answer-row svelte-1avee4x"><span class="demo-ans-same svelte-1avee4x">← LEFT is longer</span></div></div> <div class="rules-grid svelte-1avee4x"><div class="rule-card svelte-1avee4x"><span class="rule-icon svelte-1avee4x">👁️</span> <div class="rule-text svelte-1avee4x"><strong class="svelte-1avee4x">Step 1: Watch</strong> <span class="svelte-1avee4x">Two lines flash very briefly — as short as 50ms</span></div></div> <div class="rule-card svelte-1avee4x"><span class="rule-icon svelte-1avee4x">🎭</span> <div class="rule-text svelte-1avee4x"><strong class="svelte-1avee4x">Step 2: Mask</strong> <span class="svelte-1avee4x">A pattern mask immediately covers the lines</span></div></div> <div class="rule-card svelte-1avee4x"><span class="rule-icon svelte-1avee4x">↔️</span> <div class="rule-text svelte-1avee4x"><strong class="svelte-1avee4x">Step 3: Decide</strong> <span class="svelte-1avee4x">Which line was longer — LEFT or RIGHT?</span></div></div> <div class="rule-card svelte-1avee4x"><span class="rule-icon svelte-1avee4x">🔄</span> <div class="rule-text svelte-1avee4x"><strong class="svelte-1avee4x">Step 4: Repeat</strong> <span class="svelte-1avee4x">Keep going for all ${escape_html(20)} trials</span></div></div></div> <div class="info-grid svelte-1avee4x"><div class="info-section svelte-1avee4x"><h4 class="svelte-1avee4x">💡 Perception Tips</h4> <ul class="tips-list svelte-1avee4x"><li class="svelte-1avee4x"><strong class="svelte-1avee4x">Stay relaxed:</strong> Tension reduces perceptual sensitivity</li> <li class="svelte-1avee4x"><strong class="svelte-1avee4x">Central focus:</strong> Keep eyes on the screen centre before each trial</li> <li class="svelte-1avee4x"><strong class="svelte-1avee4x">Trust instincts:</strong> Go with your first impression — don't overthink</li> <li class="svelte-1avee4x"><strong class="svelte-1avee4x">It's OK to guess:</strong> Some trials are genuinely at your threshold</li></ul></div> <div class="info-section svelte-1avee4x"><h4 class="svelte-1avee4x">📋 Test Format</h4> <ul class="structure-list svelte-1avee4x"><li class="svelte-1avee4x"><span class="struct-key svelte-1avee4x">Trials</span><span class="struct-val svelte-1avee4x">${escape_html(20)}</span></li> <li class="svelte-1avee4x"><span class="struct-key svelte-1avee4x">Flash duration</span><span class="struct-val svelte-1avee4x">${escape_html(100)}ms</span></li> <li class="svelte-1avee4x"><span class="struct-key svelte-1avee4x">Mask duration</span><span class="struct-val svelte-1avee4x">${escape_html(500)}ms</span></li> <li class="svelte-1avee4x"><span class="struct-key svelte-1avee4x">Measures</span><span class="struct-val svelte-1avee4x">perceptual speed</span></li></ul></div></div> <div class="clinical-info svelte-1avee4x"><h4 class="svelte-1avee4x">🏥 Clinical Significance</h4> <div class="clinical-grid svelte-1avee4x"><div class="clinical-item svelte-1avee4x"><strong class="svelte-1avee4x">Pure Perception</strong> <span class="svelte-1avee4x">Measures basic visual processing speed — no motor component</span></div> <div class="clinical-item svelte-1avee4x"><strong class="svelte-1avee4x">MS Sensitive</strong> <span class="svelte-1avee4x">Processing speed is one of the most affected domains in MS</span></div> <div class="clinical-item svelte-1avee4x"><strong class="svelte-1avee4x">No Motor Bias</strong> <span class="svelte-1avee4x">Physical limitations don't affect this measure</span></div> <div class="clinical-item svelte-1avee4x"><strong class="svelte-1avee4x">Research Backed</strong> <span class="svelte-1avee4x">Vickers &amp; Smith (1986), widely used in neuropsychology</span></div></div></div> <div class="perf-guide svelte-1avee4x"><h4 class="svelte-1avee4x">📊 Performance Targets</h4> <div class="norm-bars svelte-1avee4x"><div class="norm-bar norm-excellent svelte-1avee4x"><span class="norm-label svelte-1avee4x">Excellent</span> <span class="norm-val svelte-1avee4x">≥90% accuracy</span></div> <div class="norm-bar norm-good svelte-1avee4x"><span class="norm-label svelte-1avee4x">Good</span> <span class="norm-val svelte-1avee4x">75–89% accuracy</span></div> <div class="norm-bar norm-avg svelte-1avee4x"><span class="norm-label svelte-1avee4x">Average</span> <span class="norm-val svelte-1avee4x">60–74% accuracy</span></div> <div class="norm-bar norm-fair svelte-1avee4x"><span class="norm-label svelte-1avee4x">Fair</span> <span class="norm-val svelte-1avee4x">50–59% accuracy</span></div> <div class="norm-bar norm-needs svelte-1avee4x"><span class="norm-label svelte-1avee4x">Developing</span> <span class="norm-val svelte-1avee4x">&lt;50% accuracy</span></div></div> <p class="norm-note svelte-1avee4x">*Scores depend on presentation time — faster flash = harder task</p></div> <div class="button-group svelte-1avee4x"><button class="btn-secondary svelte-1avee4x">✏️ Try Practice First</button> `);
          TaskPracticeActions($$renderer2, {
            locale: store_get($$store_subs ??= {}, "$locale", locale),
            startLabel: "Start Actual Task",
            practiceVisible: false,
            statusMessage: practiceStatusMessage,
            align: "center"
          });
          $$renderer2.push(`<!----></div></div>`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
