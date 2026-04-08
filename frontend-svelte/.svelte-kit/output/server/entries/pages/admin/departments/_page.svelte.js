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
    $$renderer2.push(`<div class="admin-layout svelte-zzb9uj"><aside class="sidebar svelte-zzb9uj"><div class="sidebar-brand svelte-zzb9uj"><span class="brand-icon svelte-zzb9uj">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-zzb9uj"><a href="/admin/dashboard" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item active svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-zzb9uj"><span class="nav-icon svelte-zzb9uj">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-zzb9uj"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-zzb9uj"><header class="topbar svelte-zzb9uj"><h1 class="page-title svelte-zzb9uj">Department Management</h1> <div class="admin-info svelte-zzb9uj"><span class="admin-avatar">🏥</span> <span>${escape_html(admin?.email)}</span></div></header> <div class="content svelte-zzb9uj">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <section class="create-card svelte-zzb9uj"><h2 class="svelte-zzb9uj">Create Department</h2> <div class="form-grid svelte-zzb9uj"><input type="text" placeholder="Department name"${attr("value", form.name)} class="svelte-zzb9uj"/> <input type="text" placeholder="Description (optional)"${attr("value", form.description)} class="svelte-zzb9uj"/> <button class="primary-btn svelte-zzb9uj"${attr("disabled", saving, true)}>${escape_html("Create Department")}</button></div></section> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-msg svelte-zzb9uj">Loading departments...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
