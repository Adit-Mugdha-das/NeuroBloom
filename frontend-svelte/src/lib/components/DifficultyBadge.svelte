<script>
	import { formatNumber, locale, localeText } from '$lib/i18n';
	import { getPatientDifficultyLabel, getPatientDomainLabel } from '$lib/patient-copy.js';

	export let difficulty = 5;
	export let domain = '';

	$: label = getPatientDifficultyLabel(difficulty, $locale);
	$: domainLabel = domain ? getPatientDomainLabel(domain, $locale) : '';
	$: difficultyLabel = localeText({ en: 'Level', bn: 'লেভেল' }, $locale);
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
