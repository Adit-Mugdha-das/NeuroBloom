import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let admin = null;
    $$renderer2.push(`<div class="admin-layout svelte-dndwm1"><aside class="sidebar svelte-dndwm1"><div class="sidebar-brand svelte-dndwm1"><span class="brand-icon svelte-dndwm1">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-dndwm1"><a href="/admin/dashboard" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item active svelte-dndwm1"><span class="nav-icon svelte-dndwm1">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-dndwm1"><span class="nav-icon svelte-dndwm1">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-dndwm1"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-dndwm1"><header class="topbar svelte-dndwm1"><div><h1 class="page-title svelte-dndwm1">System Health Monitoring</h1> <p class="page-sub svelte-dndwm1">Enterprise infrastructure visibility for API availability, database health, live activity, and server uptime</p></div> <div class="admin-info svelte-dndwm1">${escape_html(admin?.email)}</div></header> <div class="content svelte-dndwm1">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-dndwm1">Loading system health...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
