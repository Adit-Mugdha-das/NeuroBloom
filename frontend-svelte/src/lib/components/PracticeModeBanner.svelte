<script>
	import { getPracticeCopy } from '$lib/task-practice';

	export let locale = 'en';

	$: practiceCopy = getPracticeCopy(locale);
</script>

<div class="practice-banner" role="status" aria-live="polite">
	<div class="badge">?</div>
	<div class="copy">
		<div class="title">{practiceCopy.bannerTitle}</div>
		<div class="text">{practiceCopy.bannerText}</div>
	</div>
</div>

<style>
	.practice-banner {
		display: flex;
		align-items: center;
		gap: 0.85rem;
		margin-bottom: 1rem;
		padding: 0.9rem 1rem;
		border-radius: 14px;
		background: #fffbeb;
		border: 1px solid #fde68a;
		color: #92400e;
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
</style>
