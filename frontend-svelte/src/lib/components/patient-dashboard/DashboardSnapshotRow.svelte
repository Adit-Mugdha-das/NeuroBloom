<script>
	export let label = '';
	export let title = '';
	export let cards = [];
</script>

<section class="snapshot-shell">
	<div class="snapshot-head">
		<p class="label">{label}</p>
		<h3>{title}</h3>
	</div>

	<div class="snapshot-grid">
		{#each cards as card}
			<article class="snapshot-card">
				<p class="eyebrow">{card.eyebrow}</p>
				<h4>{card.title}</h4>
				<p class="meta">{card.meta}</p>
			</article>
		{/each}
	</div>
</section>

<style>
	.snapshot-shell {
		padding: 1.2rem 1.25rem;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.88);
		border: 1px solid rgba(203, 213, 225, 0.72);
		box-shadow: 0 16px 34px rgba(15, 23, 42, 0.05);
		display: grid;
		gap: 0.95rem;
	}

	.label,
	h3,
	.eyebrow,
	h4,
	.meta {
		margin: 0;
	}

	.label {
		font-size: 0.76rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #0369a1;
	}

	h3 {
		margin-top: 0.25rem;
		font-size: 1.3rem;
		color: #0f172a;
	}

	.snapshot-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.85rem;
	}

	.snapshot-card {
		padding: 0.95rem 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.78);
		display: grid;
		gap: 0.35rem;
	}

	.eyebrow {
		font-size: 0.76rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: #64748b;
	}

	h4 {
		font-size: 1rem;
		line-height: 1.3;
		color: #0f172a;
	}

	.meta {
		font-size: 0.9rem;
		line-height: 1.45;
		color: #64748b;
	}

	@media (max-width: 1024px) {
		.snapshot-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 640px) {
		.snapshot-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
