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
    $$renderer2.push(`<div class="admin-layout svelte-zmgv5w"><aside class="sidebar svelte-zmgv5w"><div class="sidebar-brand svelte-zmgv5w"><span class="brand-icon">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-zmgv5w"><a href="/admin/dashboard" class="nav-item svelte-zmgv5w"><span class="nav-icon">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-zmgv5w"><span class="nav-icon">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-zmgv5w"><span class="nav-icon">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-zmgv5w"><span class="nav-icon">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-zmgv5w"><span class="nav-icon">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-zmgv5w"><span class="nav-icon">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-zmgv5w"><span class="nav-icon">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-zmgv5w"><span class="nav-icon">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-zmgv5w"><span class="nav-icon">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item active svelte-zmgv5w"><span class="nav-icon">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-zmgv5w"><span class="nav-icon">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-zmgv5w"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-zmgv5w"><header class="topbar svelte-zmgv5w"><div><h1 class="page-title svelte-zmgv5w">Notification Center</h1> <p class="page-sub svelte-zmgv5w">Publish system announcements, new feature updates, and research invitations from one professional admin surface.</p></div> <div class="admin-info svelte-zmgv5w">${escape_html(admin?.email)}</div></header> <div class="content svelte-zmgv5w">`);
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
      $$renderer2.push(`<div class="loading-state svelte-zmgv5w">Loading notification center...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
