import { e as ensure_array_like, a as attr_class, c as stringify } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import { a as attr } from "../../../../chunks/attributes.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/api.js";
import { e as escape_html } from "../../../../chunks/escaping.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalActive, totalInactive;
    let admin = null;
    let patients = [];
    let searchQuery = "";
    let filter = "all";
    patients.filter((patient) => {
      const query = searchQuery.toLowerCase();
      const matchesSearch = !query || (patient.email || "").toLowerCase().includes(query) || (patient.full_name || "").toLowerCase().includes(query) || (patient.diagnosis || "").toLowerCase().includes(query);
      return matchesSearch;
    });
    totalActive = patients.filter((patient) => patient.is_active).length;
    totalInactive = patients.filter((patient) => !patient.is_active).length;
    $$renderer2.push(`<div class="admin-layout svelte-1upoz9k"><aside class="sidebar svelte-1upoz9k"><div class="sidebar-brand svelte-1upoz9k">NeuroBloom Admin</div> <nav class="sidebar-nav svelte-1upoz9k"><a href="/admin/dashboard" class="nav-item svelte-1upoz9k">Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-1upoz9k">System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-1upoz9k">Doctor Management</a> <a href="/admin/patients" class="nav-item active svelte-1upoz9k">Patient Management</a> <a href="/admin/departments" class="nav-item svelte-1upoz9k">Departments</a> <a href="/admin/interventions" class="nav-item svelte-1upoz9k">Interventions</a> <a href="/admin/messages" class="nav-item svelte-1upoz9k">Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-1upoz9k">Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-1upoz9k">System Health</a> <a href="/admin/notifications" class="nav-item svelte-1upoz9k">Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-1upoz9k">Research Data</a></nav> <button class="logout-btn svelte-1upoz9k">Logout</button></aside> <main class="main-content svelte-1upoz9k"><header class="topbar svelte-1upoz9k"><div><h1 class="page-title svelte-1upoz9k">Patient Management</h1> <p class="page-sub svelte-1upoz9k">View and control all patient accounts</p></div> <div class="admin-info svelte-1upoz9k">${escape_html(admin?.email)}</div></header> <div class="content svelte-1upoz9k">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="stats-strip svelte-1upoz9k"><div class="stat-chip svelte-1upoz9k"><p class="chip-val svelte-1upoz9k">${escape_html(patients.length)}</p> <p class="chip-lbl svelte-1upoz9k">Total</p></div> <div class="stat-chip svelte-1upoz9k"><p class="chip-val svelte-1upoz9k">${escape_html(totalActive)}</p> <p class="chip-lbl svelte-1upoz9k">Active</p></div> <div class="stat-chip svelte-1upoz9k"><p class="chip-val svelte-1upoz9k">${escape_html(totalInactive)}</p> <p class="chip-lbl svelte-1upoz9k">Inactive</p></div></div> <div class="toolbar svelte-1upoz9k"><input class="search-input svelte-1upoz9k" type="text" placeholder="Search by name, email or diagnosis..."${attr("value", searchQuery)}/> <div class="filter-tabs svelte-1upoz9k"><!--[-->`);
    const each_array = ensure_array_like([
      ["all", "All"],
      ["active", "Active"],
      ["inactive", "Inactive"]
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let [value, label] = each_array[$$index];
      $$renderer2.push(`<button type="button"${attr_class(`tab-btn ${stringify(filter === value ? "active" : "")}`, "svelte-1upoz9k")}>${escape_html(label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-msg svelte-1upoz9k">Loading patients...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
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
