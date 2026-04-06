<script>
	import { createEventDispatcher } from 'svelte';
	import { getPracticeCopy } from '$lib/task-practice';

	export let locale = 'en';
	export let startLabel = 'Start Task';
	export let disabled = false;
	export let practiceVisible = true;
	export let statusMessage = '';
	export let align = 'stretch';

	const dispatch = createEventDispatcher();

	$: practiceCopy = getPracticeCopy(locale);

	function handleStart() {
		dispatch('start');
	}

	function handlePractice() {
		dispatch('practice');
	}
</script>

<div class="practice-actions {align === 'center' ? 'align-center' : ''}">
	{#if statusMessage}
		<div class="status-message">{statusMessage}</div>
	{/if}

	<div class="button-row">
		<button class="start-button" disabled={disabled} on:click={handleStart}>
			{startLabel}
		</button>

		{#if practiceVisible}
			<button class="practice-button" disabled={disabled} on:click={handlePractice}>
				? {practiceCopy.trigger}
			</button>
		{/if}
	</div>

	{#if practiceVisible}
		<p class="practice-helper">{practiceCopy.helper}</p>
	{/if}
</div>

<style>
	.practice-actions {
		margin-top: 1.5rem;
	}

	.practice-actions.align-center {
		text-align: center;
	}

	.status-message {
		margin-bottom: 0.9rem;
		padding: 0.85rem 1rem;
		border-radius: 12px;
		background: #e8f5e9;
		color: #1b5e20;
		font-weight: 600;
	}

	.button-row {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	button {
		border: none;
		border-radius: 12px;
		padding: 0.95rem 1.35rem;
		font-size: 1rem;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
	}

	button:hover:enabled {
		transform: translateY(-1px);
	}

	button:disabled {
		cursor: not-allowed;
		opacity: 0.7;
	}

	.start-button {
		background: #2563eb;
		color: white;
		box-shadow: 0 10px 22px rgba(37, 99, 235, 0.18);
	}

	.practice-button {
		background: #eef2ff;
		color: #312e81;
		border: 1px solid rgba(99, 102, 241, 0.2);
	}

	.practice-helper {
		margin: 0.75rem 0 0;
		font-size: 0.95rem;
		color: #64748b;
	}

	@media (max-width: 640px) {
		.button-row {
			flex-direction: column;
		}
	}
</style>
