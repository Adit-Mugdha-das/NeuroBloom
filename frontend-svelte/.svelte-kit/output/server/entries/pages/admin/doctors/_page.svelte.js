import { X as ensure_array_like, U as attr_class, V as stringify } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let admin = null;
    let filter = "all";
    $$renderer2.push(`<div class="admin-layout svelte-1i2swnj"><aside class="sidebar svelte-1i2swnj"><div class="sidebar-brand svelte-1i2swnj"><span class="brand-icon svelte-1i2swnj">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-1i2swnj"><a href="/admin/dashboard" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item active svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-1i2swnj"><span class="nav-icon svelte-1i2swnj">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-1i2swnj"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-1i2swnj"><header class="topbar svelte-1i2swnj"><h1 class="page-title svelte-1i2swnj">Doctor Management</h1> <div class="admin-info svelte-1i2swnj"><span class="admin-avatar svelte-1i2swnj">🏥</span> <span>${escape_html(admin?.email)}</span></div></header> <div class="content svelte-1i2swnj">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="filter-tabs svelte-1i2swnj"><!--[-->`);
    const each_array = ensure_array_like([
      ["all", "All"],
      ["pending", "Pending Approval"],
      ["active", "Active"],
      ["suspended", "Suspended"]
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let [val, label] = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`tab-btn ${stringify(filter === val ? "active" : "")}`, "svelte-1i2swnj")}>${escape_html(label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-msg svelte-1i2swnj">Loading doctors…</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _page as default
};
