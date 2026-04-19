<script>
	export let label = '';
	export let title = '';
	export let items = [];
</script>

<section class="section-card">
	<p class="label">{label}</p>
	<h3>{title}</h3>

	<div class="area-list">
		{#each items as item}
			<a class="area-row" href={item.href}>
				<div class="area-copy">
					<p class="area-title">{item.title}</p>
					<p class="area-description">{item.description}</p>
				</div>
				<div class="area-meta">
					<span class:done={item.complete} class:pending={!item.complete}>{item.status}</span>
					<span class="area-arrow" aria-hidden="true">›</span>
				</div>
			</a>
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
		color: #7c3aed;
	}

	h3 {
		margin: 0.4rem 0 0;
		font-size: 1.7rem;
		color: #0f172a;
	}

	.area-list {
		margin-top: 1rem;
		display: grid;
		gap: 0.8rem;
	}

	.area-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
		text-decoration: none;
		color: inherit;
	}

	.area-copy {
		display: grid;
		gap: 0.25rem;
	}

	.area-title,
	.area-description {
		margin: 0;
	}

	.area-title {
		font-size: 1.02rem;
		font-weight: 800;
		color: #0f172a;
	}

	.area-description {
		font-size: 0.96rem;
		line-height: 1.55;
		color: #475569;
	}

	.area-meta {
		display: flex;
		align-items: center;
		gap: 0.7rem;
		flex-shrink: 0;
	}

	.area-meta span:first-child {
		padding: 0.35rem 0.7rem;
		border-radius: 999px;
		font-size: 0.82rem;
		font-weight: 800;
		white-space: nowrap;
	}

	.done {
		background: rgba(34, 197, 94, 0.14);
		color: #15803d;
	}

	.pending {
		background: rgba(148, 163, 184, 0.14);
		color: #475569;
	}

	.area-arrow {
		font-size: 1.4rem;
		color: #64748b;
	}

	@media (max-width: 720px) {
		.area-row {
			align-items: flex-start;
		}

		.area-meta {
			flex-direction: column;
			align-items: flex-end;
		}
	}
</style>
