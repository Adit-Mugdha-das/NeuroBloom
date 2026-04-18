<script>
	import { createEventDispatcher } from 'svelte';
	import { getPracticeCopy } from '$lib/task-practice';

	export let locale = 'en';
	export let showExit = false;
	export let exitLabel = '';
	export let exitAriaLabel = '';

	const dispatch = createEventDispatcher();

	$: practiceCopy = getPracticeCopy(locale);
	$: resolvedExitLabel = exitLabel || practiceCopy.exit;
	$: resolvedExitAriaLabel = exitAriaLabel || practiceCopy.exitAriaLabel || resolvedExitLabel;

	function handleExit() {
		dispatch('exit');
	}
</script>

<div class="practice-banner">
	<div class="status-copy" role="status" aria-live="polite">
		<div class="badge">?</div>
		<div class="copy">
			<div class="title">{practiceCopy.bannerTitle}</div>
			<div class="text">{practiceCopy.bannerText}</div>
		</div>
	</div>

	{#if showExit}
		<button
			type="button"
			class="exit-button"
			aria-label={resolvedExitAriaLabel}
			on:click={handleExit}
		>
			{resolvedExitLabel}
		</button>
	{/if}
</div>

<style>
	.practice-banner {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.85rem;
		margin-bottom: 1rem;
		padding: 0.9rem 1rem;
		border-radius: 14px;
		background: #fffbeb;
		border: 1px solid #fde68a;
		color: #92400e;
	}

	.status-copy {
		display: flex;
		align-items: center;
		gap: 0.85rem;
		flex: 1;
		min-width: 0;
	}

	.badge {
		display: grid;
		place-items: center;
		width: 2rem;
		height: 2rem;
		border-radius: 999px;
		background: #f59e0b;
		color: white;
		font-weight: 700;
	}

	.title {
		font-weight: 700;
	}

	.text {
		font-size: 0.95rem;
	}

	.exit-button {
		flex-shrink: 0;
		border: 1px solid rgba(146, 64, 14, 0.18);
		border-radius: 999px;
		padding: 0.45rem 0.75rem;
		background: rgba(255, 255, 255, 0.7);
		color: inherit;
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
		transition: background 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
	}

	.exit-button:hover {
		background: rgba(255, 255, 255, 0.95);
		border-color: rgba(146, 64, 14, 0.3);
		transform: translateY(-1px);
	}

	.exit-button:focus-visible {
		outline: 2px solid rgba(146, 64, 14, 0.35);
		outline-offset: 2px;
	}

	@media (max-width: 640px) {
		.practice-banner {
			align-items: stretch;
		}

		.status-copy {
			align-items: flex-start;
		}
	}
</style>
