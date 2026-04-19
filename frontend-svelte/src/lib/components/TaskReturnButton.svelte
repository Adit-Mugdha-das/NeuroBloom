<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { translateText } from '$lib/i18n';
	import { resolveTaskReturn, TASK_RETURN_CONTEXT } from '$lib/task-navigation';

	export let locale = 'en';
	export let context = TASK_RETURN_CONTEXT.TRAINING;

	function t(text) {
		return translateText(text ?? '', locale);
	}

	$: returnState = resolveTaskReturn($page.url, context);

	function handleReturn() {
		goto(returnState.href);
	}
</script>

<div class="task-return">
	<button type="button" class="task-return-button" on:click={handleReturn}>
		{t(returnState.labelKey)}
	</button>
</div>

<style>
	.task-return {
		display: flex;
		justify-content: flex-start;
		margin-bottom: 1rem;
	}

	.task-return-button {
		border: 1px solid rgba(15, 23, 42, 0.14);
		border-radius: 999px;
		padding: 0.65rem 1rem;
		background: rgba(255, 255, 255, 0.96);
		color: #1e293b;
		font-size: 0.92rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
		transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
	}

	.task-return-button:hover {
		transform: translateY(-1px);
		border-color: rgba(37, 99, 235, 0.3);
		box-shadow: 0 14px 28px rgba(15, 23, 42, 0.12);
	}

	.task-return-button:focus-visible {
		outline: 2px solid rgba(37, 99, 235, 0.35);
		outline-offset: 2px;
	}
	@media (max-width: 640px) {
		.task-return-button {
			width: 100%;
			justify-content: center;
		}
	}
</style>
