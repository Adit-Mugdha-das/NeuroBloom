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
    let cutoff, filtered;
    let admin = null;
    let allInterventions = [];
    let periodDays = 30;
    function buildUniqueDoctors(interventions) {
      const seen = {};
      const result = [];
      for (const i of interventions) {
        if (!seen[i.doctor_id]) {
          seen[i.doctor_id] = true;
          result.push({ id: i.doctor_id, name: i.doctor_name });
        }
      }
      return result.sort(function(a, b) {
        return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
      });
    }
    cutoff = new Date(Date.now() - periodDays * 864e5);
    filtered = allInterventions.filter(function(i) {
      if (cutoff && new Date(i.created_at) < cutoff) return false;
      return true;
    });
    buildUniqueDoctors(allInterventions);
    [
      ...new Set(allInterventions.map(function(i) {
        return i.intervention_type;
      }))
    ];
    filtered.filter(function(i) {
      return i.intervention_type.indexOf("admin_") !== 0;
    }).length;
    $$renderer2.push(`<div class="admin-layout svelte-7anotu"><aside class="sidebar svelte-7anotu"><div class="sidebar-brand svelte-7anotu"><span class="brand-icon svelte-7anotu">🏥</span> <span class="brand-name">NeuroBloom Admin</span></div> <nav class="sidebar-nav svelte-7anotu"><a href="/admin/dashboard" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">📊</span> Dashboard</a> <a href="/admin/analytics" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">📈</span> System Analytics</a> <a href="/admin/doctors" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">👨‍⚕️</span> Doctor Management</a> <a href="/admin/patients" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">👤</span> Patient Management</a> <a href="/admin/departments" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">🏢</span> Departments</a> <a href="/admin/interventions" class="nav-item active svelte-7anotu"><span class="nav-icon svelte-7anotu">🩺</span> Interventions</a> <a href="/admin/messages" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">💬</span> Message Audit</a> <a href="/admin/audit-logs" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">📋</span> Audit Logs</a> <a href="/admin/system-health" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">🖥️</span> System Health</a> <a href="/admin/notifications" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">🔔</span> Notification Center</a> <a href="/admin/research-data" class="nav-item svelte-7anotu"><span class="nav-icon svelte-7anotu">🧪</span> Research Data</a></nav> <button class="logout-btn svelte-7anotu"><span>🚪</span> Logout</button></aside> <main class="main-content svelte-7anotu"><header class="topbar svelte-7anotu"><div><h1 class="page-title svelte-7anotu">Intervention Monitoring</h1> <p class="page-sub svelte-7anotu">Clinical quality oversight of all doctor-patient interventions</p></div> <div class="admin-info svelte-7anotu">${escape_html(
      /** @type {Array<[number, string]>} */
      admin?.email
    )}</div></header> <div class="content svelte-7anotu">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading-state svelte-7anotu">Loading interventions...</div>`);
    }
    $$renderer2.push(`<!--]--></div></main></div>`);
  });
}
export {
  _page as default
};
