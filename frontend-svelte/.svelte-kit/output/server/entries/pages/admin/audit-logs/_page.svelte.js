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
    $$renderer2.push(`<div class="admin-layout svelte-j8xf1e"><aside class="sidebar svelte-j8xf1e"><div class="sidebar-brand svelte-j8xf1e"><span class="brand-icon svelte-j8xf1e">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-j8xf1e"><a href="/admin/dashboard" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item active svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-j8xf1e"><span class="nav-icon svelte-j8xf1e">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-j8xf1e"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-j8xf1e"><header class="topbar svelte-j8xf1e"><div><h1 class="page-title svelte-j8xf1e">Audit Logs</h1> <p class="page-sub svelte-j8xf1e">System activity traceability across training, clinical actions, communication, and administrative operations</p></div> <div class="admin-info svelte-j8xf1e">${escape_html(admin?.email)}</div></header> <div class="content svelte-j8xf1e">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-j8xf1e">Loading audit logs...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
