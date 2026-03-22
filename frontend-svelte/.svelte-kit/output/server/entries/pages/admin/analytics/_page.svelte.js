import { e as ensure_array_like } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { Chart, registerables } from "chart.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    Chart.register(...registerables);
    let admin = null;
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="admin-layout svelte-h1vjnr"><aside class="sidebar svelte-h1vjnr"><div class="sidebar-brand svelte-h1vjnr"><span class="brand-icon svelte-h1vjnr">🏥</span> <span class="brand-name svelte-h1vjnr">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-h1vjnr"><a href="/admin/dashboard" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item active svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-h1vjnr"><span class="nav-icon svelte-h1vjnr">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-h1vjnr"><span class="svelte-h1vjnr">🚪</span> Logout</button></aside> <main class="main-content svelte-h1vjnr"><header class="topbar svelte-h1vjnr"><div class="svelte-h1vjnr"><h1 class="page-title svelte-h1vjnr">System Analytics</h1> <p class="page-subtitle svelte-h1vjnr">Focused system-wide analytics page with only the core operational and clinical trends.</p></div> <div class="admin-info svelte-h1vjnr"><span class="admin-avatar svelte-h1vjnr">🏥</span> <span class="svelte-h1vjnr">${escape_html(admin?.email)}</span></div></header> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-grid svelte-h1vjnr"><!--[-->`);
      const each_array = ensure_array_like(Array(6));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        each_array[$$index];
        $$renderer2.push(`<div class="stat-card skeleton svelte-h1vjnr"></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
  });
}
export {
  _page as default
};
