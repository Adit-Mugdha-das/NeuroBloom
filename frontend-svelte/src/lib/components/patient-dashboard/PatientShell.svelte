<script>
	import PatientTopbar from '$lib/components/patient-dashboard/PatientTopbar.svelte';

	export let header = { brand: 'NeuroBloom', title: '', subtitle: '', logoutLabel: 'Logout' };
	export let actions = [];
	export let warnings = [];
</script>

<div class="patient-shell" data-localize-skip>
	<div class="patient-shell__inner">
		<PatientTopbar
			brand={header.brand}
			title={header.title}
			subtitle={header.subtitle}
			logoutLabel={header.logoutLabel}
			{actions}
			on:logout
		/>

		{#if warnings.length > 0}
			<section class="status-banner" role="status" aria-live="polite">
				<p>{warnings[0]}</p>
			</section>
		{/if}

		<div class="patient-layout">
			<div class="patient-main patient-main--top">
				<slot name="main-top" />
			</div>

			<aside class="patient-rail">
				<slot name="rail" />
			</aside>

			<div class="patient-main patient-main--bottom">
				<slot name="main-bottom" />
			</div>
		</div>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		background:
			radial-gradient(circle at top left, rgba(59, 130, 246, 0.08), transparent 24%),
			linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
		color: #0f172a;
	}

	.patient-shell {
		min-height: 100vh;
		padding: 1.5rem 1.25rem 3rem;
	}

	.patient-shell__inner {
		max-width: 1280px;
		margin: 0 auto;
		display: grid;
		gap: 1rem;
	}

	.status-banner {
		padding: 1rem 1.1rem;
		border-radius: 18px;
		color: #92400e;
		background: rgba(255, 251, 235, 0.98);
		border: 1px solid rgba(245, 158, 11, 0.35);
	}

	.status-banner p {
		margin: 0;
	}

	.patient-layout {
		display: grid;
		grid-template-columns: minmax(0, 1.7fr) minmax(300px, 0.84fr);
		grid-template-areas:
			'main-top rail'
			'main-bottom rail';
		align-items: start;
		gap: 1rem;
	}

	.patient-main,
	.patient-rail {
		display: grid;
		gap: 1rem;
		min-width: 0;
	}

	.patient-main--top {
		grid-area: main-top;
	}

	.patient-main--bottom {
		grid-area: main-bottom;
	}

	.patient-rail {
		grid-area: rail;
		position: sticky;
		top: 1.25rem;
	}

	@media (max-width: 1024px) {
		.patient-layout {
			grid-template-columns: minmax(0, 1fr);
			grid-template-areas:
				'main-top'
				'rail'
				'main-bottom';
		}

		.patient-rail {
			position: static;
		}
	}

	@media (max-width: 640px) {
		.patient-shell {
			padding-left: 1rem;
			padding-right: 1rem;
		}
	}
</style>
