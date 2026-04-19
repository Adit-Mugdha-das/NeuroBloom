<script>
	export let label = '';
	export let title = '';
	export let description = '';
	export let primaryAction = null;
	export let facts = [];
</script>

<section class="today-card">
	<p class="label">{label}</p>
	<h2>{title}</h2>
	<p class="description">{description}</p>

	{#if primaryAction}
		<a class="primary-action" href={primaryAction.href}>{primaryAction.label}</a>
	{/if}

	{#if facts.length > 0}
		<div class="fact-row">
			{#each facts.slice(0, 2) as fact}
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
		padding: 1.6rem;
		border-radius: 28px;
		background: linear-gradient(180deg, #ffffff, #f8fbff);
		border: 1px solid rgba(203, 213, 225, 0.8);
		box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
		display: grid;
		gap: 0.9rem;
	}

	.label {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1d4ed8;
	}

	h2 {
		margin: 0;
		font-size: clamp(2rem, 3.1vw, 2.7rem);
		line-height: 1.12;
		color: #0f172a;
		max-width: 18ch;
	}

	.description {
		margin: 0;
		max-width: 56ch;
		font-size: 1.1rem;
		line-height: 1.75;
		color: #334155;
	}

	.primary-action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: fit-content;
		min-height: 56px;
		padding: 0.95rem 1.4rem;
		border-radius: 999px;
		background: #1d4ed8;
		color: #ffffff;
		text-decoration: none;
		font-size: 1rem;
		font-weight: 800;
		box-shadow: 0 12px 28px rgba(29, 78, 216, 0.2);
	}

	.fact-row {
		display: flex;
		gap: 0.85rem;
		flex-wrap: wrap;
		margin-top: 0.2rem;
	}

	.fact-chip {
		min-width: 180px;
		padding: 0.85rem 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.85);
	}

	.fact-label,
	.fact-value {
		margin: 0;
	}

	.fact-label {
		font-size: 0.88rem;
		font-weight: 700;
		color: #64748b;
	}

	.fact-value {
		margin-top: 0.3rem;
		font-size: 1.2rem;
		font-weight: 800;
		color: #0f172a;
	}

	@media (max-width: 640px) {
		.primary-action {
			width: 100%;
		}
	}
</style>
