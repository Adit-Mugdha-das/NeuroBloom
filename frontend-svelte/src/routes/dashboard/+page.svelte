<script>
	import { goto } from '$app/navigation';
	import DashboardAreaList from '$lib/components/patient-dashboard/DashboardAreaList.svelte';
	import DashboardUtilityRail from '$lib/components/patient-dashboard/DashboardUtilityRail.svelte';
	import PatientCareDetails from '$lib/components/patient-dashboard/PatientCareDetails.svelte';
	import PatientShell from '$lib/components/patient-dashboard/PatientShell.svelte';
	import ProgressSummary from '$lib/components/patient-dashboard/ProgressSummary.svelte';
	import TodayCard from '$lib/components/patient-dashboard/TodayCard.svelte';
	import { loadPatientCareDetails } from '$lib/dashboard/patient-dashboard.js';
	import { API_BASE_URL } from '$lib/api.js';
	import { clearUser } from '$lib/stores.js';

	export let data;

	let currentUser = data.currentUser;
	let localeCode = data.localeCode;
	let dashboard = data.dashboard;
	let careDetailsOpen = false;
	let activeDashboardKey = `${data.currentUser?.id ?? ''}:${data.localeCode}`;
	let dashboardKey = activeDashboardKey;
	let careDetailsState = {
		loading: false,
		loaded: false,
		notifications: [],
		doctor: null,
		assignedDoctor: false,
		hasWarning: false
	};

	$: currentUser = data.currentUser;
	$: localeCode = data.localeCode;
	$: dashboard = data.dashboard;
	$: dashboardKey = `${data.currentUser?.id ?? ''}:${data.localeCode}`;
	$: if (dashboardKey !== activeDashboardKey) {
		careDetailsState = {
			loading: false,
			loaded: false,
			notifications: [],
			doctor: null,
			assignedDoctor: false,
			hasWarning: false
		};
		careDetailsOpen = false;
		activeDashboardKey = dashboardKey;
	}
	$: if (careDetailsOpen && !careDetailsState.loaded && !careDetailsState.loading) {
		hydrateCareDetails();
	}

	async function hydrateCareDetails() {
		careDetailsState = { ...careDetailsState, loading: true };

		try {
			const details = await loadPatientCareDetails({
				fetchImpl: window.fetch.bind(window),
				userId: currentUser.id,
				locale: localeCode
			});

			careDetailsState = {
				loading: false,
				loaded: true,
				notifications: details.notifications,
				doctor: details.doctor,
				assignedDoctor: details.assignedDoctor,
				hasWarning: details.hasWarning
			};
		} catch (_error) {
			careDetailsState = {
				loading: false,
				loaded: true,
				notifications: [],
				doctor: null,
				assignedDoctor: false,
				hasWarning: true
			};
		}
	}

	function handleLogout() {
		clearUser();
		goto('/login');
	}

	$: prescriptionPdfUrl =
		currentUser?.id && dashboard?.careSummary?.latestPrescription?.id
			? `${API_BASE_URL}/api/auth/patient/${currentUser.id}/prescriptions/${dashboard.careSummary.latestPrescription.id}/pdf`
			: '';
</script>

<PatientShell
	header={dashboard.header}
	actions={dashboard.headerActions}
	warnings={dashboard.warnings}
	on:logout={handleLogout}
>
	<div slot="main-top" class="main-column">
		<TodayCard
			label={dashboard.today.label}
			title={dashboard.today.title}
			description={dashboard.today.description}
			primaryAction={dashboard.today.action}
			facts={dashboard.today.facts}
		/>

		<ProgressSummary
			label={dashboard.progress.label}
			title={dashboard.progress.title}
			metrics={dashboard.progress.metrics}
		/>
	</div>

	<div slot="rail" class="utility-rail">
		<DashboardUtilityRail
			label={dashboard.rail.label}
			title={dashboard.rail.title}
			items={dashboard.rail.items}
			detailsLabel={dashboard.rail.detailsLabel}
			bind:detailsOpen={careDetailsOpen}
		>
			{#if careDetailsState.loading || (careDetailsOpen && !careDetailsState.loaded)}
				<div class="care-loading">
					<p>{localeCode === 'bn' ? 'বিস্তারিত লোড হচ্ছে...' : 'Loading care details...'}</p>
				</div>
			{:else}
				<PatientCareDetails
					localeCode={localeCode}
					notifications={careDetailsState.notifications}
					latestPrescription={dashboard.careSummary.latestPrescription}
					doctor={careDetailsState.doctor}
					assignedDoctor={careDetailsState.assignedDoctor}
					hasWarning={careDetailsState.hasWarning}
					prescriptionPdfUrl={prescriptionPdfUrl}
				/>
			{/if}
		</DashboardUtilityRail>
	</div>

	<div slot="main-bottom" class="main-column">
		<DashboardAreaList
			label={dashboard.areas.label}
			title={dashboard.areas.title}
			items={dashboard.areas.items}
		/>
	</div>
</PatientShell>

<style>
	.main-column,
	.utility-rail {
		display: grid;
		gap: 1rem;
	}

	.care-loading {
		padding: 1rem 1.1rem;
		border-radius: 18px;
		background: #ffffff;
		border: 1px solid rgba(203, 213, 225, 0.85);
	}

	.care-loading p {
		margin: 0;
		font-size: 0.98rem;
		font-weight: 700;
		color: #475569;
	}
</style>
