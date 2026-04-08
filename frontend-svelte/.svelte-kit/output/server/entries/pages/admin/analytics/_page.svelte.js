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
    $$renderer2.push(`<div class="admin-layout svelte-1mqs2k0"><aside class="sidebar svelte-1mqs2k0"><div class="sidebar-brand svelte-1mqs2k0"><span class="brand-icon svelte-1mqs2k0">🏥</span> <span class="brand-name svelte-1mqs2k0">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-1mqs2k0"><a href="/admin/dashboard" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item active svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-1mqs2k0"><span class="nav-icon svelte-1mqs2k0">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-1mqs2k0"><span class="svelte-1mqs2k0">🚪</span> Logout</button></aside> <main class="main-content svelte-1mqs2k0"><header class="topbar svelte-1mqs2k0"><div class="svelte-1mqs2k0"><h1 class="page-title svelte-1mqs2k0">System Analytics</h1> <p class="page-subtitle svelte-1mqs2k0">Focused system-wide analytics page with only the core operational and clinical trends.</p></div> <div class="admin-info svelte-1mqs2k0"><span class="admin-avatar svelte-1mqs2k0">🏥</span> <span class="svelte-1mqs2k0">${escape_html(admin?.email)}</span></div></header> `);
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
      $$renderer2.push(`<div class="loading-grid svelte-1mqs2k0"><!--[-->`);
      const each_array = ensure_array_like(Array(6));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        each_array[$$index];
        $$renderer2.push(`<div class="stat-card skeleton svelte-1mqs2k0"></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></main></div>`);
  });
}
export {
  _page as default
};
