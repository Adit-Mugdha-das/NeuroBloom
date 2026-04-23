<script>
	export let stats = [];
</script>

{#if stats.length > 0}
	<section class="stats-row" aria-label="Dashboard summary">
		{#each stats as stat}
			<article class="stat-chip">
				<p class="stat-label">{stat.label}</p>
				<strong class="stat-value">{stat.value}</strong>
			</article>
		{/each}
	</section>
{/if}

<style>
	.stats-row {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.8rem;
	}

	.stat-chip {
		padding: 0.95rem 1rem;
		border-radius: 20px;
		background: rgba(255, 255, 255, 0.88);
		border: 1px solid rgba(203, 213, 225, 0.75);
		box-shadow: 0 14px 32px rgba(15, 23, 42, 0.04);
		display: grid;
		gap: 0.3rem;
	}

	.stat-label,
	.stat-value {
		margin: 0;
	}

	.stat-label {
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #64748b;
	}

	.stat-value {
		font-size: 1.05rem;
		line-height: 1.3;
		color: #0f172a;
	}

	@media (max-width: 960px) {
		.stats-row {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 640px) {
		.stats-row {
			grid-template-columns: 1fr;
		}
	}
</style>
