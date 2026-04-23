<script>
	import { goto } from '$app/navigation';
	import DashboardPulseCard from '$lib/components/patient-dashboard/DashboardPulseCard.svelte';
	import DashboardStatsRow from '$lib/components/patient-dashboard/DashboardStatsRow.svelte';
	import PatientShell from '$lib/components/patient-dashboard/PatientShell.svelte';
	import TodayCard from '$lib/components/patient-dashboard/TodayCard.svelte';
	import { clearUser } from '$lib/stores.js';

	export let data;

	let dashboard = data.dashboard;

	$: dashboard = data.dashboard;

	function handleLogout() {
		clearUser();
		goto('/login');
	}
</script>

<PatientShell
	header={{ ...dashboard.header, description: '' }}
	actions={dashboard.headerActions}
	warnings={dashboard.warnings}
	layout="single"
	on:logout={handleLogout}
>
	<div slot="main-top" class="dashboard-stack">
		<TodayCard
			label={dashboard.hero.label}
			title={dashboard.hero.title}
			description={dashboard.hero.description}
			status={dashboard.hero.status}
			primaryAction={dashboard.hero.primaryAction}
			secondaryAction={dashboard.hero.secondaryAction}
			facts={dashboard.hero.facts}
		/>

		<DashboardStatsRow stats={dashboard.todayStats} />
	</div>

	<div slot="main-bottom" class="dashboard-stack">
		<DashboardPulseCard
			label={dashboard.progressPulse.label}
			title={dashboard.progressPulse.title}
			metrics={dashboard.progressPulse.metrics}
			action={dashboard.progressPulse.action}
			tone={dashboard.progressPulse.tone}
		/>

		<DashboardPulseCard
			label={dashboard.carePulse.label}
			title={dashboard.carePulse.title}
			metrics={dashboard.carePulse.metrics}
			action={dashboard.carePulse.action}
			tone={dashboard.carePulse.tone}
		/>

		{#if dashboard.insightPulse}
			<DashboardPulseCard
				label={dashboard.insightPulse.label}
				title={dashboard.insightPulse.title}
				metrics={dashboard.insightPulse.metrics}
				action={dashboard.insightPulse.action}
				tone={dashboard.insightPulse.tone}
			/>
		{/if}
	</div>
</PatientShell>

<style>
	.dashboard-stack {
		display: grid;
		gap: 1rem;
	}
</style>
