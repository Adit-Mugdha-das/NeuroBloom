<script>
	export let label = '';
	export let title = '';
	export let cards = [];
</script>

<section class="rail-panel">
	<p class="label">{label}</p>
	<h2>{title}</h2>

	<div class="rail-list">
		{#each cards as card}
			<article class="rail-card">
				<p class="card-eyebrow">{card.eyebrow}</p>
				<h3>{card.title}</h3>
				<p class="card-body">{card.body}</p>

				{#if card.action}
					<a class="card-action" href={card.action.href}>{card.action.label}</a>
				{/if}
			</article>
		{/each}
	</div>
</section>

<style>
	.rail-panel {
		padding: 1.25rem;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(203, 213, 225, 0.82);
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.05);
		display: grid;
		gap: 1rem;
	}

	.label,
	h2,
	.card-eyebrow,
	h3,
	.card-body {
		margin: 0;
	}

	.label {
		font-size: 0.88rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #0f766e;
	}

	h2 {
		font-size: 1.4rem;
		color: #0f172a;
	}

	.rail-list {
		display: grid;
		gap: 0.8rem;
	}

	.rail-card {
		padding: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.82);
		display: grid;
		gap: 0.45rem;
	}

	.card-eyebrow {
		font-size: 0.8rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
	}

	h3 {
		font-size: 1rem;
		line-height: 1.35;
		color: #0f172a;
	}

	.card-body {
		font-size: 0.94rem;
		line-height: 1.58;
		color: #475569;
	}

	.card-action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: fit-content;
		margin-top: 0.2rem;
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

	@media (max-width: 720px) {
		.card-action {
			width: 100%;
		}
	}
</style>
