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
    let cutoff, loweredQuery;
    let admin = null;
    let allLogs = [];
    let periodDays = 30;
    let searchQuery = "";
    cutoff = new Date(Date.now() - periodDays * 864e5);
    loweredQuery = searchQuery.trim().toLowerCase();
    allLogs.filter((log) => {
      if (cutoff && new Date(log.created_at) < cutoff) return false;
      if (!loweredQuery) return true;
      return [
        log.actor_name || "",
        log.target_name || "",
        log.summary || "",
        log.detail || "",
        log.badge || ""
      ].some((value) => value.toLowerCase().includes(loweredQuery));
    });
    [...new Set(allLogs.map((log) => log.category))];
    $$renderer2.push(`<div class="admin-layout svelte-7oozap"><aside class="sidebar svelte-7oozap"><div class="sidebar-brand svelte-7oozap"><span class="brand-icon svelte-7oozap">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-7oozap"><a href="/admin/dashboard" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item active svelte-7oozap"><span class="nav-icon svelte-7oozap">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-7oozap"><span class="nav-icon svelte-7oozap">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-7oozap"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-7oozap"><header class="topbar svelte-7oozap"><div><h1 class="page-title svelte-7oozap">Audit Logs</h1> <p class="page-sub svelte-7oozap">System activity traceability across training, clinical actions, communication, and administrative operations</p></div> <div class="admin-info svelte-7oozap">${escape_html(admin?.email)}</div></header> <div class="content svelte-7oozap">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-7oozap">Loading audit logs...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
