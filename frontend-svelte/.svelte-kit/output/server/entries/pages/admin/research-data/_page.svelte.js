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
    $$renderer2.push(`<div class="admin-layout svelte-7vvinb"><aside class="sidebar svelte-7vvinb"><div class="sidebar-brand svelte-7vvinb"><span class="brand-icon">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-7vvinb"><a href="/admin/dashboard" class="nav-item svelte-7vvinb"><span class="nav-icon">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-7vvinb"><span class="nav-icon">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-7vvinb"><span class="nav-icon">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-7vvinb"><span class="nav-icon">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-7vvinb"><span class="nav-icon">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-7vvinb"><span class="nav-icon">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-7vvinb"><span class="nav-icon">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-7vvinb"><span class="nav-icon">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-7vvinb"><span class="nav-icon">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-7vvinb"><span class="nav-icon">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item active svelte-7vvinb"><span class="nav-icon">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-7vvinb"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-7vvinb"><header class="topbar svelte-7vvinb"><div><h1 class="page-title svelte-7vvinb">Research Data Exports</h1> <p class="page-sub svelte-7vvinb">Export anonymized NeuroBloom datasets for research papers, secondary analysis, and institutional reporting.</p></div> <div class="admin-info svelte-7vvinb">${escape_html(admin?.email)}</div></header> <div class="content svelte-7vvinb">`);
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
      $$renderer2.push(`<div class="loading-state svelte-7vvinb">Loading research export catalog...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
