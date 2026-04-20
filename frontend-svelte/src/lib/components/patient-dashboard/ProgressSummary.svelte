<script>
	export let label = '';
	export let title = '';
	export let description = '';
	export let cards = [];
	export let links = [];
</script>

<section class="section-card">
	<div class="section-head">
		<div class="section-copy">
			<p class="label">{label}</p>
			<h3>{title}</h3>
			{#if description}
				<p class="description">{description}</p>
			{/if}
		</div>

		{#if links.length > 0}
			<div class="link-row">
				{#each links as link}
					<a href={link.href}>{link.label}</a>
				{/each}
			</div>
		{/if}
	</div>

	<div class="cards-grid">
		{#each cards as card}
			<article class="summary-card">
				<p class="card-eyebrow">{card.eyebrow}</p>
				<h4>{card.title}</h4>
				<p class="card-description">{card.description}</p>
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
		display: grid;
		gap: 1rem;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
	}

	.section-copy {
		display: grid;
		gap: 0.35rem;
	}

	.label,
	h3,
	.description,
	.card-eyebrow,
	h4,
	.card-description {
		margin: 0;
	}

	.label {
		font-size: 0.88rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #0369a1;
	}

	h3 {
		font-size: 1.7rem;
		color: #0f172a;
	}

	.description {
		max-width: 58ch;
		font-size: 0.98rem;
		line-height: 1.6;
		color: #475569;
	}

	.link-row {
		display: flex;
		gap: 0.65rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.link-row a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 42px;
		padding: 0.72rem 0.9rem;
		border-radius: 999px;
		background: rgba(239, 246, 255, 0.92);
		border: 1px solid rgba(147, 197, 253, 0.5);
		color: #0f172a;
		text-decoration: none;
		font-weight: 800;
		font-size: 0.88rem;
	}

	.cards-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.summary-card {
		padding: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
		display: grid;
		gap: 0.35rem;
	}

	.card-eyebrow {
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: #0f766e;
	}

	h4 {
		font-size: 1.02rem;
		line-height: 1.35;
		color: #0f172a;
	}

	.card-description {
		font-size: 0.94rem;
		line-height: 1.58;
		color: #475569;
	}

	@media (max-width: 1024px) {
		.cards-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 720px) {
		.section-head {
			flex-direction: column;
		}

		.link-row {
			justify-content: flex-start;
		}

		.cards-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
