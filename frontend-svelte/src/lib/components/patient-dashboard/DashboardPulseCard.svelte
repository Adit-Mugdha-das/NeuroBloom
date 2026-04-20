<script>
	export let label = '';
	export let title = '';
	export let tone = 'default';
	export let metrics = [];
	export let action = null;
</script>

<section class="pulse-card {tone}">
	<div class="pulse-head">
		<div class="pulse-copy">
			{#if label}
				<p class="pulse-label">{label}</p>
			{/if}
			<h3>{title}</h3>
		</div>

		{#if action}
			<a class="pulse-link" href={action.href}>{action.label}</a>
		{/if}
	</div>

	{#if metrics.length > 0}
		<div class="metric-grid">
			{#each metrics as metric}
				<div class="metric-card">
					<p class="metric-label">{metric.label}</p>
					<strong class="metric-value">{metric.value}</strong>
				</div>
			{/each}
		</div>
	{/if}
</section>

<style>
	.pulse-card {
		padding: 1.15rem;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(203, 213, 225, 0.8);
		box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
		display: grid;
		gap: 0.95rem;
	}

	.pulse-card.progress {
		background:
			radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 28%),
			rgba(255, 255, 255, 0.94);
	}

	.pulse-card.care {
		background:
			radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 28%),
			rgba(255, 255, 255, 0.94);
	}

	.pulse-card.insight {
		background:
			radial-gradient(circle at top right, rgba(249, 115, 22, 0.08), transparent 28%),
			rgba(255, 255, 255, 0.94);
	}

	.pulse-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.pulse-copy {
		display: grid;
		gap: 0.25rem;
	}

	.pulse-label,
	h3,
	.metric-label,
	.metric-value {
		margin: 0;
	}

	.pulse-label {
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #2563eb;
	}

	h3 {
		font-size: 1.15rem;
		line-height: 1.35;
		color: #0f172a;
	}

	.pulse-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 42px;
		padding: 0.72rem 0.92rem;
		border-radius: 999px;
		text-decoration: none;
		font-size: 0.88rem;
		font-weight: 800;
		color: #0f172a;
		background: rgba(248, 250, 252, 0.94);
		border: 1px solid rgba(148, 163, 184, 0.55);
	}

	.metric-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.8rem;
	}

	.metric-card {
		padding: 0.9rem 0.95rem;
		border-radius: 18px;
		background: rgba(248, 250, 252, 0.9);
		border: 1px solid rgba(203, 213, 225, 0.74);
		display: grid;
		gap: 0.3rem;
	}

	.metric-label {
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #64748b;
	}

	.metric-value {
		font-size: 1rem;
		line-height: 1.35;
		color: #0f172a;
	}

	@media (max-width: 900px) {
		.metric-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 640px) {
		.pulse-head {
			flex-direction: column;
		}

		.pulse-link {
			width: 100%;
		}
	}
</style>
