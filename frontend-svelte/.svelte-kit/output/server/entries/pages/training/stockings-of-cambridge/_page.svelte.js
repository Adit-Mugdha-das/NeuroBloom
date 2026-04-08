import { s as store_get, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
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
    $$renderer2.push(`<div class="soc-page svelte-6y72ef" data-localize-skip=""><div class="soc-wrapper svelte-6y72ef">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="header-card svelte-6y72ef"><div class="header-content svelte-6y72ef"><div class="header-text svelte-6y72ef"><h1 class="task-title svelte-6y72ef">${escape_html(lt("Stockings of Cambridge", "স্টকিংস অব কেমব্রিজ"))}</h1> <p class="task-domain svelte-6y72ef">${escape_html(lt("Planning / Executive Function", "পরিকল্পনা / নির্বাহী কার্যকারিতা"))}</p></div> `);
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
        $$renderer2.push(`<div class="card task-concept svelte-6y72ef"><div class="concept-badge svelte-6y72ef"><span class="badge-icon svelte-6y72ef">SOC</span> <span class="svelte-6y72ef">${escape_html(lt("Executive Planning", "নির্বাহী পরিকল্পনা"))}</span></div> <p class="concept-desc svelte-6y72ef">${escape_html(lt("The Stockings of Cambridge is a CANTAB variant of the Tower of London. Move coloured balls between stockings to match a target arrangement in the minimum number of moves. It measures planning, working memory, and prefrontal executive function — domains frequently impaired in multiple sclerosis.", "স্টকিংস অব কেমব্রিজ হলো টাওয়ার অব লন্ডনের একটি CANTAB রূপ। সর্বনিম্ন পদক্ষেপে রঙিন বল রিঅ্যারেঞ্জ করে লক্ষ্য বিন্যাসের সাথে মেলাতে হয়। এটি পরিকল্পনা, ওয়ার্কিং মেমোরি এবং প্রিফ্রন্টাল নির্বাহী কার্যকারিতা পরিমাপ করে।"))}</p></div> <div class="card svelte-6y72ef"><h2 class="section-title svelte-6y72ef">${escape_html(lt("How to Play", "কীভাবে খেলবেন"))}</h2> <div class="rules-grid svelte-6y72ef"><div class="rule-item svelte-6y72ef"><div class="rule-num svelte-6y72ef">1</div> <div class="rule-text svelte-6y72ef"><strong class="svelte-6y72ef">${escape_html(lt("Study start and goal", "শুরু এবং লক্ষ্য পর্যবেক্ষণ করুন"))}</strong> <span class="svelte-6y72ef">${escape_html(lt("Both stocking configurations are shown during the planning phase. Memorise the goal layout.", "পরিকল্পনা পর্যায়ে উভয় বিন্যাস দেখানো হয়। লক্ষ্য বিন্যাস মনে রাখুন।"))}</span></div></div> <div class="rule-item svelte-6y72ef"><div class="rule-num svelte-6y72ef">2</div> <div class="rule-text svelte-6y72ef"><strong class="svelte-6y72ef">${escape_html(lt("Plan before moving", "চলার আগে পরিকল্পনা করুন"))}</strong> <span class="svelte-6y72ef">${escape_html(lt("Work out the full move sequence in your head before touching any ball.", "কোনো বল স্পর্শ করার আগে সম্পূর্ণ পদক্ষেপের ক্রম মাথায় নির্ধারণ করুন।"))}</span></div></div> <div class="rule-item svelte-6y72ef"><div class="rule-num svelte-6y72ef">3</div> <div class="rule-text svelte-6y72ef"><strong class="svelte-6y72ef">${escape_html(lt("Click ball, then click stocking", "বল ক্লিক করুন তারপর স্টকিং ক্লিক করুন"))}</strong> <span class="svelte-6y72ef">${escape_html(lt("Select the top ball in any stocking, then click the destination stocking to place it.", "যেকোনো স্টকিংয়ের সবচেয়ে উপরের বলটি নির্বাচন করুন, তারপর গন্তব্য স্টকিংয়ে ক্লিক করুন।"))}</span></div></div> <div class="rule-item svelte-6y72ef"><div class="rule-num svelte-6y72ef">4</div> <div class="rule-text svelte-6y72ef"><strong class="svelte-6y72ef">${escape_html(lt("Respect capacity limits", "ধারণক্ষমতার সীমা মানুন"))}</strong> <span class="svelte-6y72ef">${escape_html(lt("Stocking 1 holds 3 balls, Stocking 2 holds 2, Stocking 3 holds only 1. Full stockings refuse new balls.", "স্টকিং ১ — ৩টি, স্টকিং ২ — ২টি, স্টকিং ৩ — ১টি বল ধারণ করে। পূর্ণ স্টকিং নতুন বল গ্রহণ করে না।"))}</span></div></div></div></div> <div class="card svelte-6y72ef"><h2 class="section-title svelte-6y72ef">${escape_html(lt("Stocking Capacities", "স্টকিংয়ের ধারণক্ষমতা"))}</h2> <div class="cap-row svelte-6y72ef"><div class="cap-item svelte-6y72ef"><div class="cap-circle cap-1 svelte-6y72ef">3</div> <div class="cap-label svelte-6y72ef">${escape_html(lt("Stocking 1", "স্টকিং ১"))}</div> <div class="cap-sub svelte-6y72ef">${escape_html(lt("3 balls max", "সর্বোচ্চ ৩টি"))}</div></div> <div class="cap-arrow svelte-6y72ef">→</div> <div class="cap-item svelte-6y72ef"><div class="cap-circle cap-2 svelte-6y72ef">2</div> <div class="cap-label svelte-6y72ef">${escape_html(lt("Stocking 2", "স্টকিং ২"))}</div> <div class="cap-sub svelte-6y72ef">${escape_html(lt("2 balls max", "সর্বোচ্চ ২টি"))}</div></div> <div class="cap-arrow svelte-6y72ef">→</div> <div class="cap-item svelte-6y72ef"><div class="cap-circle cap-3 svelte-6y72ef">1</div> <div class="cap-label svelte-6y72ef">${escape_html(lt("Stocking 3", "স্টকিং ৩"))}</div> <div class="cap-sub svelte-6y72ef">${escape_html(lt("1 ball max", "সর্বোচ্চ ১টি"))}</div></div></div></div> <div class="info-grid svelte-6y72ef"><div class="card svelte-6y72ef"><h3 class="card-title svelte-6y72ef">${escape_html(lt("Session Details", "সেশনের বিবরণ"))}</h3> <div class="details-list svelte-6y72ef"><div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Problems", "সমস্যা"))}</span> <strong class="svelte-6y72ef">${escape_html("—")}</strong></div> <div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Planning Time", "পরিকল্পনার সময়"))}</span> <strong class="svelte-6y72ef">${escape_html("—")}</strong></div> <div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Difficulty", "কঠিনতা"))}</span> <strong class="svelte-6y72ef">${escape_html(lt(`Level ${difficulty} / 10`, `লেভেল ${difficulty} / ১০`))}</strong></div> <div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Problem Type", "সমস্যার ধরন"))}</span> <strong class="svelte-6y72ef">${escape_html(getDifficultyInfo())}</strong></div> `);
        {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></div></div> <div class="card svelte-6y72ef"><h3 class="card-title svelte-6y72ef">${escape_html(lt("What It Measures", "এটি কী পরিমাপ করে"))}</h3> <div class="details-list svelte-6y72ef"><div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Primary Metric", "প্রাথমিক মেট্রিক"))}</span> <strong class="svelte-6y72ef">${escape_html(lt("Planning efficiency", "পরিকল্পনা দক্ষতা"))}</strong></div> <div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Cognitive Domain", "জ্ঞানীয় ডোমেইন"))}</span> <strong class="svelte-6y72ef">${escape_html(lt("Executive function", "নির্বাহী কার্যকারিতা"))}</strong></div> <div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Scoring Basis", "স্কোরিং ভিত্তি"))}</span> <strong class="svelte-6y72ef">${escape_html(lt("Moves used vs minimum", "ব্যবহৃত বনাম সর্বনিম্ন"))}</strong></div> <div class="detail-row svelte-6y72ef"><span class="svelte-6y72ef">${escape_html(lt("Test Battery", "পরীক্ষার ব্যাটারি"))}</span> <strong class="svelte-6y72ef">CANTAB</strong></div></div></div></div> <div class="clinical-info svelte-6y72ef"><div class="clinical-header svelte-6y72ef"><div class="clinical-badge svelte-6y72ef">${escape_html(lt("Clinical Basis", "ক্লিনিকাল ভিত্তি"))}</div> <h3 class="svelte-6y72ef">${escape_html(lt("CANTAB Gold Standard Planning Test", "CANTAB গোল্ড স্ট্যান্ডার্ড পরিকল্পনা পরীক্ষা"))}</h3></div> <p class="svelte-6y72ef">${escape_html(lt("Owen et al. (1990) introduced the Stockings of Cambridge as the CANTAB computerised version of the Tower of London. MS patients show significantly more excess moves and longer thinking times, with performance correlating with lesion load in frontal and parietal white matter. The task is included in the BICAMS cognitive battery for MS.", "ওয়েন et al. (১৯৯০) টাওয়ার অব লন্ডনের CANTAB কম্পিউটারাইজড সংস্করণ হিসেবে স্টকিংস অব কেমব্রিজ প্রবর্তন করেন। এমএস রোগীরা উল্লেখযোগ্যভাবে বেশি অতিরিক্ত পদক্ষেপ করেন। পারফরম্যান্স ফ্রন্টাল এবং প্যারিটাল সাদা পদার্থে লেশন লোডের সাথে সম্পর্কিত।"))}</p></div> <div class="card perf-guide svelte-6y72ef"><h3 class="card-title svelte-6y72ef">${escape_html(lt("Planning Efficiency Norms", "পরিকল্পনা দক্ষতার নির্দেশিকা"))}</h3> <p class="perf-subtitle svelte-6y72ef">${escape_html(lt("Minimum moves / moves used (higher = better)", "সর্বনিম্ন পদক্ষেপ / ব্যবহৃত পদক্ষেপ (বেশি = ভালো)"))}</p> <div class="norm-bars svelte-6y72ef"><div class="norm-bar svelte-6y72ef"><div class="norm-label svelte-6y72ef">${escape_html(lt("Excellent", "উৎকৃষ্ট"))}</div> <div class="norm-track svelte-6y72ef"><div class="norm-fill norm-excellent svelte-6y72ef"></div></div> <div class="norm-range svelte-6y72ef">> 80%</div></div> <div class="norm-bar svelte-6y72ef"><div class="norm-label svelte-6y72ef">${escape_html(lt("Normal", "স্বাভাবিক"))}</div> <div class="norm-track svelte-6y72ef"><div class="norm-fill norm-normal svelte-6y72ef"></div></div> <div class="norm-range svelte-6y72ef">60–80%</div></div> <div class="norm-bar svelte-6y72ef"><div class="norm-label svelte-6y72ef">${escape_html(lt("Impaired", "দুর্বল"))}</div> <div class="norm-track svelte-6y72ef"><div class="norm-fill norm-impaired svelte-6y72ef"></div></div> <div class="norm-range svelte-6y72ef">&lt; 60%</div></div></div></div> `);
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
      $$renderer2.push(`<button class="help-fab svelte-6y72ef">?</button>`);
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
