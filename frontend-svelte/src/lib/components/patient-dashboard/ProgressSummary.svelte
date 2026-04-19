<script>
	export let label = '';
	export let title = '';
	export let metrics = [];
</script>

<section class="section-card">
	<p class="label">{label}</p>
	<h3>{title}</h3>

	<div class="metrics">
		{#each metrics.slice(0, 3) as metric}
			<article class="metric-card">
				<p class="metric-label">{metric.label}</p>
				<p class="metric-value">{metric.value}</p>
				{#if metric.note}
					<p class="metric-note">{metric.note}</p>
				{/if}
			</article>
		{/each}
	</div>
</section>

<style>
	.section-card {
		padding: 1.35rem;
		border-radius: 24px;
		background: #ffffff;
		border: 1px solid rgba(203, 213, 225, 0.8);
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.05);
	}

	.label {
		margin: 0;
		font-size: 0.88rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #0369a1;
	}

	h3 {
		margin: 0.4rem 0 0;
		font-size: 1.7rem;
		color: #0f172a;
	}

	.metrics {
		margin-top: 1rem;
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.metric-card {
		padding: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
	}

	.metric-label,
	.metric-value,
	.metric-note {
		margin: 0;
	}

	.metric-label {
		font-size: 0.95rem;
		font-weight: 700;
		color: #475569;
	}

	.metric-value {
		margin-top: 0.45rem;
		font-size: 1.95rem;
		font-weight: 800;
		color: #0f172a;
	}

	.metric-note {
		margin-top: 0.45rem;
		font-size: 0.94rem;
		line-height: 1.55;
		color: #64748b;
	}

	@media (max-width: 900px) {
		.metrics {
			grid-template-columns: 1fr;
		}
	}
</style>
