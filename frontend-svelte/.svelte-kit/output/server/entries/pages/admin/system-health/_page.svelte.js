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
    $$renderer2.push(`<div class="admin-layout svelte-p8k7ku"><aside class="sidebar svelte-p8k7ku"><div class="sidebar-brand svelte-p8k7ku"><span class="brand-icon svelte-p8k7ku">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-p8k7ku"><a href="/admin/dashboard" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item active svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-p8k7ku"><span class="nav-icon svelte-p8k7ku">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-p8k7ku"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-p8k7ku"><header class="topbar svelte-p8k7ku"><div><h1 class="page-title svelte-p8k7ku">System Health Monitoring</h1> <p class="page-sub svelte-p8k7ku">Enterprise infrastructure visibility for API availability, database health, live activity, and server uptime</p></div> <div class="admin-info svelte-p8k7ku">${escape_html(admin?.email)}</div></header> <div class="content svelte-p8k7ku">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-p8k7ku">Loading system health...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
