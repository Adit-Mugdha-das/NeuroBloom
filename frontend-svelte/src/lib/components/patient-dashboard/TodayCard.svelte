<script>
	export let label = '';
	export let title = '';
	export let description = '';
	export let status = null;
	export let primaryAction = null;
	export let secondaryAction = null;
	export let facts = [];
</script>

<section class="today-card">
	<div class="hero-copy">
		<p class="label">{label}</p>
		<h2>{title}</h2>
		{#if description}
			<p class="description">{description}</p>
		{/if}
	</div>

	{#if status}
		<div class="status-pill">
			<p class="status-label">{status.label}</p>
			<p class="status-value">{status.value}</p>
		</div>
	{/if}

	<div class="action-row">
		{#if primaryAction}
			<a class="primary-action" href={primaryAction.href}>{primaryAction.label}</a>
		{/if}
		{#if secondaryAction}
			<a class="secondary-action" href={secondaryAction.href}>{secondaryAction.label}</a>
		{/if}
	</div>

	{#if facts.length > 0}
		<div class="fact-row">
			{#each facts as fact}
				<div class="fact-chip">
					<p class="fact-label">{fact.label}</p>
					<p class="fact-value">{fact.value}</p>
				</div>
			{/each}
		</div>
	{/if}
</section>

<style>
	.today-card {
		padding: 1.3rem;
		border-radius: 28px;
		background:
			radial-gradient(circle at top right, rgba(56, 189, 248, 0.12), transparent 24%),
			linear-gradient(180deg, #ffffff, #f8fbff);
		border: 1px solid rgba(203, 213, 225, 0.82);
		box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
		display: grid;
		gap: 0.9rem;
	}

	.hero-copy {
		display: grid;
		gap: 0.45rem;
	}

	.label,
	h2,
	.description,
	.status-label,
	.status-value,
	.fact-label,
	.fact-value {
		margin: 0;
	}

	.label {
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1d4ed8;
	}

	h2 {
		font-size: clamp(1.75rem, 3vw, 2.35rem);
		line-height: 1.12;
		color: #0f172a;
		max-width: 18ch;
	}

	.description {
		max-width: 54ch;
		font-size: 0.96rem;
		line-height: 1.55;
		color: #334155;
	}

	.status-pill {
		width: fit-content;
		padding: 0.75rem 0.95rem;
		border-radius: 18px;
		background: rgba(239, 246, 255, 0.9);
		border: 1px solid rgba(147, 197, 253, 0.45);
	}

	.status-label {
		font-size: 0.82rem;
		font-weight: 700;
		color: #1d4ed8;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.status-value {
		margin-top: 0.3rem;
		font-size: 0.96rem;
		font-weight: 800;
		color: #0f172a;
	}

	.action-row {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.primary-action,
	.secondary-action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 48px;
		padding: 0.8rem 1.05rem;
		border-radius: 999px;
		text-decoration: none;
		font-size: 0.92rem;
		font-weight: 800;
	}

	.primary-action {
		background: #1d4ed8;
		color: #ffffff;
		box-shadow: 0 12px 28px rgba(29, 78, 216, 0.2);
	}

	.secondary-action {
		background: rgba(255, 255, 255, 0.9);
		color: #0f172a;
		border: 1px solid rgba(148, 163, 184, 0.75);
	}

	.fact-row {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.75rem;
	}

	.fact-chip {
		padding: 0.82rem 0.92rem;
		border-radius: 18px;
		background: rgba(248, 250, 252, 0.92);
		border: 1px solid rgba(203, 213, 225, 0.82);
	}

	.fact-label {
		font-size: 0.78rem;
		font-weight: 700;
		color: #64748b;
	}

	.fact-value {
		margin-top: 0.35rem;
		font-size: 1rem;
		font-weight: 800;
		color: #0f172a;
	}

	@media (max-width: 900px) {
		.fact-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 640px) {
		.today-card {
			padding: 1.15rem;
		}

		.status-pill,
		.primary-action,
		.secondary-action {
			width: 100%;
		}

		.action-row {
			display: grid;
		}
	}
</style>
