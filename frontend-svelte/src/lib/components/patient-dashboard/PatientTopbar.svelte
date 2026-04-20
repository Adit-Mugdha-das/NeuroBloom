<script>
	import { createEventDispatcher } from 'svelte';

	export let brand = 'NeuroBloom';
	export let title = '';
	export let subtitle = '';
	export let description = '';
	export let actions = [];
	export let logoutLabel = 'Logout';

	const dispatch = createEventDispatcher();

	function isUtilityAction(action) {
		return action?.type === 'logout';
	}
</script>

<header class="patient-topbar">
	<div class="topbar-copy">
		<p class="brand-mark">{brand}</p>
		<h1>{title}</h1>
		{#if subtitle}
			<p class="subtitle">{subtitle}</p>
		{/if}
		{#if description}
			<p class="description">{description}</p>
		{/if}
	</div>

	<div class="topbar-actions">
		{#each actions as action}
			{#if isUtilityAction(action)}
				<button class="action-pill utility" type="button" on:click={() => dispatch('logout')}>
					<span class="action-label">{action.label || logoutLabel}</span>
				</button>
			{:else}
				<a class="action-pill" href={action.href}>
					<span class="action-label">{action.label}</span>
					{#if action.badge}
						<span class="action-badge">{action.badge}</span>
					{/if}
				</a>
			{/if}
		{/each}
	</div>
</header>

<style>
	.patient-topbar {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1.25rem;
	}

	.topbar-copy {
		display: grid;
		gap: 0.35rem;
		min-width: 0;
	}

	.brand-mark,
	h1,
	.subtitle,
	.description {
		margin: 0;
	}

	.brand-mark {
		font-size: 0.88rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #2563eb;
	}

	h1 {
		font-size: clamp(2rem, 3vw, 2.8rem);
		line-height: 1.08;
		color: #0f172a;
	}

	.subtitle {
		font-size: 1rem;
		font-weight: 700;
		line-height: 1.4;
		color: #0f172a;
	}

	.description {
		font-size: 0.98rem;
		line-height: 1.6;
		color: #64748b;
		max-width: 44rem;
	}

	.topbar-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.65rem;
		justify-content: flex-end;
	}

	.action-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.55rem;
		min-height: 46px;
		padding: 0.8rem 1rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(203, 213, 225, 0.9);
		text-decoration: none;
		color: #0f172a;
		font-weight: 800;
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
	}

	.action-pill.utility {
		cursor: pointer;
	}

	.action-label {
		font-size: 0.95rem;
	}

	.action-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.55rem;
		height: 1.55rem;
		padding: 0 0.35rem;
		border-radius: 999px;
		background: #1d4ed8;
		color: #ffffff;
		font-size: 0.8rem;
		line-height: 1;
	}

	@media (max-width: 960px) {
		.patient-topbar {
			flex-direction: column;
		}

		.topbar-actions {
			justify-content: flex-start;
		}
	}

	@media (max-width: 640px) {
		.topbar-actions {
			display: grid;
			grid-template-columns: repeat(2, minmax(0, 1fr));
			width: 100%;
		}

		.action-pill {
			width: 100%;
		}
	}
</style>
