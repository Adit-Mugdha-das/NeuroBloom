import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import { B as BadgeNotification } from "../../../../chunks/BadgeNotification.js";
import { D as DifficultyBadge } from "../../../../chunks/DifficultyBadge.js";
/* empty css                                                               */
import { P as PracticeModeBanner } from "../../../../chunks/PracticeModeBanner.js";
import { T as TaskPracticeActions } from "../../../../chunks/TaskPracticeActions.js";
import { t as translateText, l as locale, a as localeText, f as formatNumber } from "../../../../chunks/index3.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    let newBadges = [];
    let playMode = TASK_PLAY_MODE.RECORDED;
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
    function difficultySummary() {
      {
        return lt("Single digit numbers, clear cues (2 seconds)", "এক অঙ্কের সংখ্যা, স্পষ্ট সংকেত (২ সেকেন্ড)");
      }
    }
    user.subscribe((value) => {
    });
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="pm-page svelte-1ak4y2" data-localize-skip=""><div class="pm-wrapper svelte-1ak4y2">`);
    {
      $$renderer2.push("<!--[!-->");
      {
        $$renderer2.push("<!--[!-->");
        {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="header-card svelte-1ak4y2"><div class="header-content svelte-1ak4y2"><div class="header-text svelte-1ak4y2"><h1 class="task-title svelte-1ak4y2">${escape_html(t("Plus-Minus Task"))}</h1> <p class="task-domain svelte-1ak4y2">${escape_html(lt("Cognitive Flexibility", "জ্ঞানীয় নমনীয়তা"))}</p></div> `);
          DifficultyBadge($$renderer2, { difficulty, domain: "Cognitive Flexibility" });
          $$renderer2.push(`<!----></div></div> `);
          if (playMode === TASK_PLAY_MODE.PRACTICE) {
            $$renderer2.push("<!--[-->");
            PracticeModeBanner($$renderer2, { locale: store_get($$store_subs ??= {}, "$locale", locale) });
          } else {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--> <div class="card task-concept svelte-1ak4y2"><div class="concept-badge svelte-1ak4y2"><span class="badge-icon svelte-1ak4y2">+/-</span> <span class="svelte-1ak4y2">${escape_html(lt("Switching Paradigm", "স্যুইচিং প্যারাডাইম"))}</span></div> <p class="concept-desc svelte-1ak4y2">${escape_html(lt("The Plus-Minus Task measures cognitive switching cost — the time penalty you pay when alternating between mental operations. Jersild (1927) first described switching costs; Miyake et al. (2000) established shifting as a core executive function reliably impaired in multiple sclerosis.", "প্লাস-মাইনাস টাস্কটি জ্ঞানীয় স্যুইচিং কস্ট পরিমাপ করে — মানসিক অপারেশন পরিবর্তন করার সময় যে সময়-জরিমানা হয়। মাল্টিপল স্ক্লেরোসিস গবেষণায় এটি একটি মূল এক্সিকিউটিভ ফাংশন পরিমাপক।"))}</p></div> <div class="card svelte-1ak4y2"><h2 class="section-title svelte-1ak4y2">${escape_html(lt("Three-Block Structure", "তিন-ব্লক কাঠামো"))}</h2> <div class="block-overview svelte-1ak4y2"><div class="block-item block-item-a svelte-1ak4y2"><span class="block-badge badge-green svelte-1ak4y2">${escape_html(lt("Block A", "ব্লক A"))}</span> <div class="block-op block-op-green svelte-1ak4y2">+3</div> <div class="block-label svelte-1ak4y2">${escape_html(lt("Add 3", "যোগ ৩"))}</div> <div class="block-desc svelte-1ak4y2">${escape_html(lt("Baseline: addition speed", "বেসলাইন: যোগের গতি"))}</div></div> <div class="block-arrow svelte-1ak4y2">→</div> <div class="block-item block-item-b svelte-1ak4y2"><span class="block-badge badge-blue svelte-1ak4y2">${escape_html(lt("Block B", "ব্লক B"))}</span> <div class="block-op block-op-blue svelte-1ak4y2">-3</div> <div class="block-label svelte-1ak4y2">${escape_html(lt("Subtract 3", "বিয়োগ ৩"))}</div> <div class="block-desc svelte-1ak4y2">${escape_html(lt("Baseline: subtraction speed", "বেসলাইন: বিয়োগের গতি"))}</div></div> <div class="block-arrow svelte-1ak4y2">→</div> <div class="block-item block-item-c svelte-1ak4y2"><span class="block-badge badge-lime svelte-1ak4y2">${escape_html(lt("Block C", "ব্লক C"))}</span> <div class="block-op block-op-lime svelte-1ak4y2">+/-</div> <div class="block-label svelte-1ak4y2">${escape_html(lt("Alternating", "পালাবদল"))}</div> <div class="block-desc svelte-1ak4y2">${escape_html(lt("Measures switching cost", "স্যুইচিং কস্ট পরিমাপ"))}</div></div></div></div> <div class="card svelte-1ak4y2"><h2 class="section-title svelte-1ak4y2">${escape_html(lt("How to Play", "কীভাবে খেলবেন"))}</h2> <div class="rules-grid svelte-1ak4y2"><div class="rule-item svelte-1ak4y2"><div class="rule-num svelte-1ak4y2">1</div> <div class="rule-text svelte-1ak4y2"><strong class="svelte-1ak4y2">${escape_html(lt("See the number", "সংখ্যাটি দেখুন"))}</strong> <span class="svelte-1ak4y2">${escape_html(lt("A number appears on screen in each trial.", "প্রতিটি ট্রায়ালে স্ক্রিনে একটি সংখ্যা দেখা যাবে।"))}</span></div></div> <div class="rule-item svelte-1ak4y2"><div class="rule-num svelte-1ak4y2">2</div> <div class="rule-text svelte-1ak4y2"><strong class="svelte-1ak4y2">${escape_html(lt("Apply the operation", "অপারেশন প্রয়োগ করুন"))}</strong> <span class="svelte-1ak4y2">${escape_html(lt("Add or subtract 3 as directed by the current block rule.", "বর্তমান ব্লকের নিয়ম অনুযায়ী ৩ যোগ বা বিয়োগ করুন।"))}</span></div></div> <div class="rule-item svelte-1ak4y2"><div class="rule-num svelte-1ak4y2">3</div> <div class="rule-text svelte-1ak4y2"><strong class="svelte-1ak4y2">${escape_html(lt("Type your answer", "আপনার উত্তর টাইপ করুন"))}</strong> <span class="svelte-1ak4y2">${escape_html(lt("Enter the result and press Enter or click Submit.", "ফলাফল লিখুন এবং Enter চাপুন বা Submit বাটনে ক্লিক করুন।"))}</span></div></div> <div class="rule-item svelte-1ak4y2"><div class="rule-num svelte-1ak4y2">4</div> <div class="rule-text svelte-1ak4y2"><strong class="svelte-1ak4y2">${escape_html(lt("Watch the cue in Block C", "ব্লক C-তে সংকেতে মনোযোগ দিন"))}</strong> <span class="svelte-1ak4y2">${escape_html(lt("A brief +3 or -3 cue flashes before each number. React quickly.", "প্রতিটি সংখ্যার আগে +৩ বা -৩ সংকেত ঝলকাবে। দ্রুত সাড়া দিন।"))}</span></div></div></div></div> <div class="info-grid svelte-1ak4y2"><div class="card svelte-1ak4y2"><h3 class="card-title svelte-1ak4y2">${escape_html(lt("Session Details", "সেশনের বিবরণ"))}</h3> <div class="details-list svelte-1ak4y2"><div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Total Trials", "মোট ট্রায়াল"))}</span> <strong class="svelte-1ak4y2">${escape_html("36")}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Blocks", "ব্লক"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt("3 (Add / Subtract / Alternating)", "৩টি (যোগ / বিয়োগ / পালাবদল)"))}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Trials per Block", "প্রতি ব্লকে ট্রায়াল"))}</span> <strong class="svelte-1ak4y2">12</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Cue Duration (Block C)", "সংকেত সময় (ব্লক C)"))}</span> <strong class="svelte-1ak4y2">${escape_html("—")}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Difficulty", "কঠিনতা"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt(`Level ${difficulty} / 10`, `লেভেল ${n(difficulty)} / ১০`))}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Number Range", "সংখ্যার পরিসর"))}</span> <strong class="svelte-1ak4y2">${escape_html(difficultySummary())}</strong></div></div></div> <div class="card svelte-1ak4y2"><h3 class="card-title svelte-1ak4y2">${escape_html(lt("What It Measures", "এটি কী পরিমাপ করে"))}</h3> <div class="details-list svelte-1ak4y2"><div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Primary Metric", "প্রাথমিক মেট্রিক"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt("Switching cost (ms)", "স্যুইচিং কস্ট (মি.সে)"))}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Cognitive Domain", "জ্ঞানীয় ডোমেইন"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt("Cognitive flexibility", "জ্ঞানীয় নমনীয়তা"))}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Baseline", "বেসলাইন"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt("Blocks A + B pure speed", "ব্লক A + B খাঁটি গতি"))}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("Switch Measure", "স্যুইচ পরিমাপ"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt("Block C minus baseline avg", "ব্লক C বিয়োগ গড় বেসলাইন"))}</strong></div> <div class="detail-row svelte-1ak4y2"><span class="svelte-1ak4y2">${escape_html(lt("MS Relevance", "এমএস প্রাসঙ্গিকতা"))}</span> <strong class="svelte-1ak4y2">${escape_html(lt("Executive function marker", "এক্সিকিউটিভ ফাংশন চিহ্নক"))}</strong></div></div></div></div> <div class="clinical-info svelte-1ak4y2"><div class="clinical-header svelte-1ak4y2"><div class="clinical-badge svelte-1ak4y2">${escape_html(lt("Clinical Basis", "ক্লিনিকাল ভিত্তি"))}</div> <h3 class="svelte-1ak4y2">${escape_html(lt("Validated Switching Paradigm", "যাচাইকৃত স্যুইচিং প্যারাডাইম"))}</h3></div> <p class="svelte-1ak4y2">${escape_html(lt("Jersild (1927) first described task-switching costs, and Miyake et al. (2000) confirmed cognitive shifting as a separable executive function. This paradigm isolates pure switching cost with minimal working memory demands, making it ideal for assessing cognitive flexibility impairment in multiple sclerosis.", "জার্সিল্ড (১৯২৭) প্রথম টাস্ক-স্যুইচিং কস্টের বর্ণনা দেন, এবং মিয়াকে এবং অন্যান্য (২০০০) জ্ঞানীয় শিফটিংকে একটি আলাদা এক্সিকিউটিভ ফাংশন হিসেবে নিশ্চিত করেন। এই প্যারাডাইমটি মাল্টিপল স্ক্লেরোসিসে জ্ঞানীয় নমনীয়তার দুর্বলতা মূল্যায়নের জন্য আদর্শ।"))}</p></div> <div class="card perf-guide svelte-1ak4y2"><h3 class="card-title svelte-1ak4y2">${escape_html(lt("Switching Cost Norms", "স্যুইচিং কস্ট নির্দেশিকা"))}</h3> <p class="perf-subtitle svelte-1ak4y2">${escape_html(lt("Block C RT minus average of Blocks A and B", "ব্লক C RT বিয়োগ ব্লক A এবং B-এর গড়"))}</p> <div class="norm-bars svelte-1ak4y2"><div class="norm-bar svelte-1ak4y2"><div class="norm-label svelte-1ak4y2">${escape_html(lt("Excellent", "উৎকৃষ্ট"))}</div> <div class="norm-track svelte-1ak4y2"><div class="norm-fill norm-excellent svelte-1ak4y2"></div></div> <div class="norm-range svelte-1ak4y2">&lt; 100 ms</div></div> <div class="norm-bar svelte-1ak4y2"><div class="norm-label svelte-1ak4y2">${escape_html(lt("Normal", "স্বাভাবিক"))}</div> <div class="norm-track svelte-1ak4y2"><div class="norm-fill norm-normal svelte-1ak4y2"></div></div> <div class="norm-range svelte-1ak4y2">100–200 ms</div></div> <div class="norm-bar svelte-1ak4y2"><div class="norm-label svelte-1ak4y2">${escape_html(lt("Elevated", "উচ্চ"))}</div> <div class="norm-track svelte-1ak4y2"><div class="norm-fill norm-elevated svelte-1ak4y2"></div></div> <div class="norm-range svelte-1ak4y2">> 200 ms</div></div></div></div> `);
          TaskPracticeActions($$renderer2, {
            locale: store_get($$store_subs ??= {}, "$locale", locale),
            startLabel: t("Start Test"),
            statusMessage: practiceStatusMessage
          });
          $$renderer2.push(`<!---->`);
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="help-fab svelte-1ak4y2">?</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    if (newBadges && newBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: newBadges });
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
