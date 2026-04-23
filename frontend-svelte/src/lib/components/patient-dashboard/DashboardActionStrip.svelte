<script>
	export let actions = [];
</script>

<section class="action-strip">
	{#each actions as action}
		<a class="action-card" href={action.href}>
			<div>
				<p class="eyebrow">{action.eyebrow}</p>
				<h3>{action.label}</h3>
			</div>
			<p class="description">{action.description}</p>
		</a>
	{/each}
</section>

<style>
	.action-strip {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.85rem;
	}

	.action-card {
		padding: 1rem;
		border-radius: 22px;
		text-decoration: none;
		background: rgba(255, 255, 255, 0.92);
		border: 1px solid rgba(203, 213, 225, 0.78);
		box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
		display: grid;
		gap: 0.55rem;
		color: inherit;
		transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
	}

	.action-card:hover {
		transform: translateY(-2px);
		border-color: rgba(96, 165, 250, 0.5);
		box-shadow: 0 20px 38px rgba(15, 23, 42, 0.08);
	}

	.eyebrow,
	h3,
	.description {
		margin: 0;
	}

	.eyebrow {
		font-size: 0.76rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #0f766e;
	}

	h3 {
		font-size: 1.02rem;
		line-height: 1.3;
		color: #0f172a;
	}

	.description {
		font-size: 0.92rem;
		line-height: 1.55;
		color: #64748b;
	}

	@media (max-width: 1024px) {
		.action-strip {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 640px) {
		.action-strip {
			grid-template-columns: 1fr;
		}
	}
</style>
