import { a as attr } from "../../../../chunks/attributes.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let admin = null;
    let saving = false;
    let form = { name: "", description: "" };
    $$renderer2.push(`<div class="admin-layout svelte-172eadc"><aside class="sidebar svelte-172eadc"><div class="sidebar-brand svelte-172eadc"><span class="brand-icon svelte-172eadc">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-172eadc"><a href="/admin/dashboard" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item active svelte-172eadc"><span class="nav-icon svelte-172eadc">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-172eadc"><span class="nav-icon svelte-172eadc">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-172eadc"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-172eadc"><header class="topbar svelte-172eadc"><h1 class="page-title svelte-172eadc">Department Management</h1> <div class="admin-info svelte-172eadc"><span class="admin-avatar">🏥</span> <span>${escape_html(admin?.email)}</span></div></header> <div class="content svelte-172eadc">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <section class="create-card svelte-172eadc"><h2 class="svelte-172eadc">Create Department</h2> <div class="form-grid svelte-172eadc"><input type="text" placeholder="Department name"${attr("value", form.name)} class="svelte-172eadc"/> <input type="text" placeholder="Description (optional)"${attr("value", form.description)} class="svelte-172eadc"/> <button class="primary-btn svelte-172eadc"${attr("disabled", saving, true)}>${escape_html("Create Department")}</button></div></section> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-msg svelte-172eadc">Loading departments...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
