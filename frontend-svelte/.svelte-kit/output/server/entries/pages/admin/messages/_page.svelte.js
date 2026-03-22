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
    let cutoff, loweredQuery, filteredMessages;
    let admin = null;
    let allMessages = [];
    let periodDays = 30;
    let searchQuery = "";
    cutoff = new Date(Date.now() - periodDays * 864e5);
    loweredQuery = searchQuery.trim().toLowerCase();
    filteredMessages = allMessages.filter((message) => {
      if (cutoff && new Date(message.created_at) < cutoff) return false;
      if (!loweredQuery) return true;
      return [
        message.sender_name,
        message.recipient_name,
        message.subject || "",
        message.message,
        message.preview
      ].some((value) => value.toLowerCase().includes(loweredQuery));
    });
    filteredMessages.filter((message) => message.audit.flagged).length;
    $$renderer2.push(`<div class="admin-layout svelte-y35r3l"><aside class="sidebar svelte-y35r3l"><div class="sidebar-brand svelte-y35r3l"><span class="brand-icon svelte-y35r3l">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-y35r3l"><a href="/admin/dashboard" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item active svelte-y35r3l"><span class="nav-icon svelte-y35r3l">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-y35r3l"><span class="nav-icon svelte-y35r3l">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-y35r3l"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-y35r3l"><header class="topbar svelte-y35r3l"><div><h1 class="page-title svelte-y35r3l">Message Audit</h1> <p class="page-sub svelte-y35r3l">Communication logging, moderation signals, and oversight across doctor-patient messaging</p></div> <div class="admin-info svelte-y35r3l">${escape_html(admin?.email)}</div></header> <div class="content svelte-y35r3l">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-y35r3l">Loading message audit...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
