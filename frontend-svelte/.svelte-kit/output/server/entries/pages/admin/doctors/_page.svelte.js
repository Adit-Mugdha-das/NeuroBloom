import { e as ensure_array_like, a as attr_class, c as stringify } from "../../../../chunks/index2.js";
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
    $$renderer2.push(`<div class="admin-layout svelte-uso548"><aside class="sidebar svelte-uso548"><div class="sidebar-brand svelte-uso548"><span class="brand-icon svelte-uso548">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-uso548"><a href="/admin/dashboard" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item active svelte-uso548"><span class="nav-icon svelte-uso548">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-uso548"><span class="nav-icon svelte-uso548">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-uso548"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-uso548"><header class="topbar svelte-uso548"><h1 class="page-title svelte-uso548">Doctor Management</h1> <div class="admin-info svelte-uso548"><span class="admin-avatar svelte-uso548">🏥</span> <span>${escape_html(admin?.email)}</span></div></header> <div class="content svelte-uso548">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="filter-tabs svelte-uso548"><!--[-->`);
    const each_array = ensure_array_like([
      ["all", "All"],
      ["pending", "Pending Approval"],
      ["active", "Active"],
      ["suspended", "Suspended"]
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let [val, label] = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`tab-btn ${stringify(filter === val ? "active" : "")}`, "svelte-uso548")}>${escape_html(label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-msg svelte-uso548">Loading doctors…</div>`);
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
