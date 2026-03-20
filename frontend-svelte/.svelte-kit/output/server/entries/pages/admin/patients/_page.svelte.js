import { X as ensure_array_like, U as attr_class, V as stringify } from "../../../../chunks/index2.js";
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
    $$renderer2.push(`<div class="admin-layout svelte-qec5db"><aside class="sidebar svelte-qec5db"><div class="sidebar-brand svelte-qec5db">NeuroBloom Admin</div> <nav class="sidebar-nav svelte-qec5db"><a href="/admin/dashboard" class="nav-item svelte-qec5db">Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-qec5db">System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-qec5db">Doctor Management</a> <a href="/admin/patients" class="nav-item active svelte-qec5db">Patient Management</a> <a href="/admin/departments" class="nav-item svelte-qec5db">Departments</a> <a href="/admin/interventions" class="nav-item svelte-qec5db">Interventions</a> <a href="/admin/messages" class="nav-item svelte-qec5db">Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-qec5db">Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-qec5db">System Health</a> <a href="/admin/notifications" class="nav-item svelte-qec5db">Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-qec5db">Research Data</a></nav> <button class="logout-btn svelte-qec5db">Logout</button></aside> <main class="main-content svelte-qec5db"><header class="topbar svelte-qec5db"><div><h1 class="page-title svelte-qec5db">Patient Management</h1> <p class="page-sub svelte-qec5db">View and control all patient accounts</p></div> <div class="admin-info svelte-qec5db">${escape_html(admin?.email)}</div></header> <div class="content svelte-qec5db">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="stats-strip svelte-qec5db"><div class="stat-chip svelte-qec5db"><p class="chip-val svelte-qec5db">${escape_html(patients.length)}</p> <p class="chip-lbl svelte-qec5db">Total</p></div> <div class="stat-chip svelte-qec5db"><p class="chip-val svelte-qec5db">${escape_html(totalActive)}</p> <p class="chip-lbl svelte-qec5db">Active</p></div> <div class="stat-chip svelte-qec5db"><p class="chip-val svelte-qec5db">${escape_html(totalInactive)}</p> <p class="chip-lbl svelte-qec5db">Inactive</p></div></div> <div class="toolbar svelte-qec5db"><input class="search-input svelte-qec5db" type="text" placeholder="Search by name, email or diagnosis..."${attr("value", searchQuery)}/> <div class="filter-tabs svelte-qec5db"><!--[-->`);
    const each_array = ensure_array_like([
      ["all", "All"],
      ["active", "Active"],
      ["inactive", "Inactive"]
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let [value, label] = each_array[$$index];
      $$renderer2.push(`<button type="button"${attr_class(`tab-btn ${stringify(filter === value ? "active" : "")}`, "svelte-qec5db")}>${escape_html(label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-msg svelte-qec5db">Loading patients...</div>`);
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
