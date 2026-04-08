import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
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
import { a as localeText, l as locale } from "../../../../chunks/index3.js";
import { T as TASK_PLAY_MODE } from "../../../../chunks/TaskPracticeActions.svelte_svelte_type_style_lang.js";
import { u as user } from "../../../../chunks/stores2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let difficulty = 1;
    let earnedBadges = [];
    let playMode = TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = "";
    user.subscribe((value) => {
      if (value) value.id;
    });
    function lt(en, bn) {
      return localeText({ en, bn }, store_get($$store_subs ??= {}, "$locale", locale));
    }
    function getDifficultyInfo() {
      return "";
    }
    $$renderer2.push(`<div class="tol-page svelte-1m3cgg7" data-localize-skip=""><div class="tol-wrapper svelte-1m3cgg7">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="header-card svelte-1m3cgg7"><div class="header-content svelte-1m3cgg7"><div class="header-text svelte-1m3cgg7"><h1 class="task-title svelte-1m3cgg7">${escape_html(lt("Tower of London", "টাওয়ার অব লন্ডন"))}</h1> <p class="task-domain svelte-1m3cgg7">${escape_html(lt("Planning / Executive Function", "পরিকল্পনা / নির্বাহী কার্যকারিতা"))}</p></div> `);
      DifficultyBadge($$renderer2, {
        difficulty,
        domain: "Executive Planning"
      });
      $$renderer2.push(`<!----></div></div> `);
      if (playMode === TASK_PLAY_MODE.PRACTICE) {
        $$renderer2.push("<!--[-->");
        PracticeModeBanner($$renderer2, { locale: store_get($$store_subs ??= {}, "$locale", locale) });
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="card task-concept svelte-1m3cgg7"><div class="concept-badge svelte-1m3cgg7"><span class="badge-icon svelte-1m3cgg7">TOL</span> <span class="svelte-1m3cgg7">${escape_html(lt("Executive Planning", "নির্বাহী পরিকল্পনা"))}</span></div> <p class="concept-desc svelte-1m3cgg7">${escape_html(lt("The Tower of London requires advance planning, working memory, and inhibitory control to move colored disks in the minimum number of steps. It is widely used to assess prefrontal-dependent planning deficits in multiple sclerosis.", "টাওয়ার অব লন্ডন সর্বনিম্ন পদক্ষেপে রঙিন ডিস্ক সরাতে অগ্রিম পরিকল্পনা, ওয়ার্কিং মেমোরি এবং বাধামূলক নিয়ন্ত্রণ প্রয়োজন। এটি মাল্টিপল স্ক্লেরোসিসে প্রিফ্রন্টাল পরিকল্পনার ঘাটতি মূল্যায়নে ব্যাপকভাবে ব্যবহৃত।"))}</p></div> <div class="card svelte-1m3cgg7"><h2 class="section-title svelte-1m3cgg7">${escape_html(lt("How to Play", "কীভাবে খেলবেন"))}</h2> <div class="rules-grid svelte-1m3cgg7"><div class="rule-item svelte-1m3cgg7"><div class="rule-num svelte-1m3cgg7">1</div> <div class="rule-text svelte-1m3cgg7"><strong class="svelte-1m3cgg7">${escape_html(lt("Study the planning screen", "পরিকল্পনার স্ক্রিন পর্যবেক্ষণ করুন"))}</strong> <span class="svelte-1m3cgg7">${escape_html(lt("The start and goal disk positions are shown side by side during the planning phase.", "পরিকল্পনা পর্যায়ে শুরু এবং লক্ষ্যের অবস্থান পাশাপাশি দেখানো হয়।"))}</span></div></div> <div class="rule-item svelte-1m3cgg7"><div class="rule-num svelte-1m3cgg7">2</div> <div class="rule-text svelte-1m3cgg7"><strong class="svelte-1m3cgg7">${escape_html(lt("Plan before moving", "চলার আগে পরিকল্পনা করুন"))}</strong> <span class="svelte-1m3cgg7">${escape_html(lt("Work out the minimum number of moves mentally before starting execution.", "চালু করার আগে মানসিকভাবে সর্বনিম্ন পদক্ষেপের সংখ্যা নির্ধারণ করুন।"))}</span></div></div> <div class="rule-item svelte-1m3cgg7"><div class="rule-num svelte-1m3cgg7">3</div> <div class="rule-text svelte-1m3cgg7"><strong class="svelte-1m3cgg7">${escape_html(lt("Click disk then click peg", "ডিস্ক ক্লিক করুন তারপর পেগ ক্লিক করুন"))}</strong> <span class="svelte-1m3cgg7">${escape_html(lt("Select the top disk on any peg, then click the destination peg to move it.", "যেকোনো পেগের উপরের ডিস্ক নির্বাচন করুন, তারপর গন্তব্য পেগে ক্লিক করুন।"))}</span></div></div> <div class="rule-item svelte-1m3cgg7"><div class="rule-num svelte-1m3cgg7">4</div> <div class="rule-text svelte-1m3cgg7"><strong class="svelte-1m3cgg7">${escape_html(lt("Respect capacity limits", "ধারণক্ষমতার সীমা মানুন"))}</strong> <span class="svelte-1m3cgg7">${escape_html(lt("Peg 1 holds 3 disks, Peg 2 holds 2, Peg 3 holds only 1. You cannot overfill a peg.", "পেগ ১ — ৩টি, পেগ ২ — ২টি, পেগ ৩ — ১টি ডিস্ক ধারণ করে। পেগ অতিরিক্ত পূর্ণ করা যাবে না।"))}</span></div></div></div></div> <div class="card svelte-1m3cgg7"><h2 class="section-title svelte-1m3cgg7">${escape_html(lt("Peg Capacities", "পেগের ধারণক্ষমতা"))}</h2> <div class="peg-cap-row svelte-1m3cgg7"><div class="peg-cap-item svelte-1m3cgg7"><div class="cap-circle cap-1 svelte-1m3cgg7">3</div> <div class="cap-label svelte-1m3cgg7">${escape_html(lt("Peg 1", "পেগ ১"))}</div> <div class="cap-sub svelte-1m3cgg7">${escape_html(lt("3 disks max", "সর্বোচ্চ ৩টি"))}</div></div> <div class="cap-arrow svelte-1m3cgg7">→</div> <div class="peg-cap-item svelte-1m3cgg7"><div class="cap-circle cap-2 svelte-1m3cgg7">2</div> <div class="cap-label svelte-1m3cgg7">${escape_html(lt("Peg 2", "পেগ ২"))}</div> <div class="cap-sub svelte-1m3cgg7">${escape_html(lt("2 disks max", "সর্বোচ্চ ২টি"))}</div></div> <div class="cap-arrow svelte-1m3cgg7">→</div> <div class="peg-cap-item svelte-1m3cgg7"><div class="cap-circle cap-3 svelte-1m3cgg7">1</div> <div class="cap-label svelte-1m3cgg7">${escape_html(lt("Peg 3", "পেগ ৩"))}</div> <div class="cap-sub svelte-1m3cgg7">${escape_html(lt("1 disk max", "সর্বোচ্চ ১টি"))}</div></div></div></div> <div class="info-grid svelte-1m3cgg7"><div class="card svelte-1m3cgg7"><h3 class="card-title svelte-1m3cgg7">${escape_html(lt("Session Details", "সেশনের বিবরণ"))}</h3> <div class="details-list svelte-1m3cgg7"><div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Problems", "সমস্যা"))}</span> <strong class="svelte-1m3cgg7">${escape_html("—")}</strong></div> <div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Planning Time", "পরিকল্পনার সময়"))}</span> <strong class="svelte-1m3cgg7">${escape_html("—")}</strong></div> <div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Difficulty", "কঠিনতা"))}</span> <strong class="svelte-1m3cgg7">${escape_html(lt(`Level ${difficulty} / 10`, `লেভেল ${difficulty} / ১০`))}</strong></div> <div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Problem Type", "সমস্যার ধরন"))}</span> <strong class="svelte-1m3cgg7">${escape_html(getDifficultyInfo())}</strong></div> `);
        {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></div></div> <div class="card svelte-1m3cgg7"><h3 class="card-title svelte-1m3cgg7">${escape_html(lt("What It Measures", "এটি কী পরিমাপ করে"))}</h3> <div class="details-list svelte-1m3cgg7"><div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Primary Metric", "প্রাথমিক মেট্রিক"))}</span> <strong class="svelte-1m3cgg7">${escape_html(lt("Planning efficiency", "পরিকল্পনা দক্ষতা"))}</strong></div> <div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Cognitive Domain", "জ্ঞানীয় ডোমেইন"))}</span> <strong class="svelte-1m3cgg7">${escape_html(lt("Executive function", "নির্বাহী কার্যকারিতা"))}</strong></div> <div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("Scoring Basis", "স্কোরিং ভিত্তি"))}</span> <strong class="svelte-1m3cgg7">${escape_html(lt("Moves used vs minimum", "ব্যবহৃত বনাম সর্বনিম্ন"))}</strong></div> <div class="detail-row svelte-1m3cgg7"><span class="svelte-1m3cgg7">${escape_html(lt("MS Relevance", "এমএস প্রাসঙ্গিকতা"))}</span> <strong class="svelte-1m3cgg7">${escape_html(lt("Prefrontal planning", "প্রিফ্রন্টাল পরিকল্পনা"))}</strong></div></div></div></div> <div class="clinical-info svelte-1m3cgg7"><div class="clinical-header svelte-1m3cgg7"><div class="clinical-badge svelte-1m3cgg7">${escape_html(lt("Clinical Basis", "ক্লিনিকাল ভিত্তি"))}</div> <h3 class="svelte-1m3cgg7">${escape_html(lt("Gold Standard Planning Paradigm", "গোল্ড স্ট্যান্ডার্ড পরিকল্পনা প্যারাডাইম"))}</h3></div> <p class="svelte-1m3cgg7">${escape_html(lt("Shallice (1982) developed the Tower of London to study frontal lobe planning. Owen et al. (1990) extended it via the CANTAB battery. MS patients make significantly more excess moves, revealing prefrontal-executive deficits that correlate with daily functioning and real-world multitasking ability.", "শ্যালিস (১৯৮২) ফ্রন্টাল লোব পরিকল্পনা অধ্যয়নের জন্য টাওয়ার অব লন্ডন তৈরি করেন। গবেষণায় দেখা গেছে এমএস রোগীরা উল্লেখযোগ্যভাবে বেশি অতিরিক্ত পদক্ষেপ করেন যা দৈনন্দিন কার্যকারিতার সাথে সম্পর্কিত।"))}</p></div> <div class="card perf-guide svelte-1m3cgg7"><h3 class="card-title svelte-1m3cgg7">${escape_html(lt("Planning Efficiency Norms", "পরিকল্পনা দক্ষতার নির্দেশিকা"))}</h3> <p class="perf-subtitle svelte-1m3cgg7">${escape_html(lt("Minimum moves / moves used (higher = better)", "সর্বনিম্ন পদক্ষেপ / ব্যবহৃত পদক্ষেপ (বেশি = ভালো)"))}</p> <div class="norm-bars svelte-1m3cgg7"><div class="norm-bar svelte-1m3cgg7"><div class="norm-label svelte-1m3cgg7">${escape_html(lt("Excellent", "উৎকৃষ্ট"))}</div> <div class="norm-track svelte-1m3cgg7"><div class="norm-fill norm-excellent svelte-1m3cgg7"></div></div> <div class="norm-range svelte-1m3cgg7">> 80%</div></div> <div class="norm-bar svelte-1m3cgg7"><div class="norm-label svelte-1m3cgg7">${escape_html(lt("Normal", "স্বাভাবিক"))}</div> <div class="norm-track svelte-1m3cgg7"><div class="norm-fill norm-normal svelte-1m3cgg7"></div></div> <div class="norm-range svelte-1m3cgg7">60–80%</div></div> <div class="norm-bar svelte-1m3cgg7"><div class="norm-label svelte-1m3cgg7">${escape_html(lt("Impaired", "দুর্বল"))}</div> <div class="norm-track svelte-1m3cgg7"><div class="norm-fill norm-impaired svelte-1m3cgg7"></div></div> <div class="norm-range svelte-1m3cgg7">&lt; 60%</div></div></div></div> `);
        TaskPracticeActions($$renderer2, {
          locale: store_get($$store_subs ??= {}, "$locale", locale),
          startLabel: lt("Start Planning Challenge", "পরিকল্পনা চ্যালেঞ্জ শুরু করুন"),
          statusMessage: practiceStatusMessage
        });
        $$renderer2.push(`<!---->`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="help-fab svelte-1m3cgg7">?</button>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    if (earnedBadges.length > 0) {
      $$renderer2.push("<!--[-->");
      BadgeNotification($$renderer2, { badges: earnedBadges });
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
