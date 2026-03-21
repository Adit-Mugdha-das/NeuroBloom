<script>
	import { formatNumber, locale, translateText } from '$lib/i18n';

	export let difficulty = 5;
	export let domain = '';

	function getDifficultyLabel(diff) {
		if (diff <= 3) return 'Easy';
		if (diff <= 6) return 'Medium';
		if (diff <= 8) return 'Hard';
		return 'Expert';
	}

	$: label = translateText(getDifficultyLabel(difficulty), $locale);
	$: domainLabel = domain ? translateText(domain, $locale) : '';
	$: difficultyLabel = translateText('Level', $locale);
	$: displayDifficulty = formatNumber(difficulty, $locale);
</script>

<div class="difficulty-badge">
	{#if domain}
		<span class="domain-label">{domainLabel}</span>
		<span class="separator">•</span>
	{/if}
	<span class="level-text">{difficultyLabel} {displayDifficulty}</span>
	<span class="level-label">({label})</span>
</div>

<style>
	.difficulty-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.4rem 0.8rem;
		border-radius: 6px;
		font-size: 0.85rem;
		font-weight: 500;
		background: #f5f5f5;
		color: #555;
		border: 1px solid #e0e0e0;
		white-space: nowrap;
	}

	.domain-label {
		color: #666;
		font-size: 0.8rem;
	}

	.separator {
		opacity: 0.4;
		font-size: 0.7rem;
	}

	.level-text {
		font-weight: 600;
		color: #333;
	}

	.level-label {
		color: #888;
		font-size: 0.75rem;
		font-weight: 400;
	}
</style>
