<script>
	export let label = '';
	export let title = '';
	export let description = '';
	export let items = [];
	export let footerAction = null;
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

		{#if footerAction}
			<a class="footer-link desktop-only" href={footerAction.href}>{footerAction.label}</a>
		{/if}
	</div>

	<div class="area-list">
		{#each items as item}
			<article class="area-card {item.tone || ''}">
				<div class="card-copy">
					<p class="area-eyebrow">{item.eyebrow}</p>
					<h4>{item.title}</h4>
					<p class="area-description">{item.description}</p>
				</div>

				{#if item.meta?.length}
					<div class="meta-row">
						{#each item.meta as meta}
							<span>{meta}</span>
						{/each}
					</div>
				{/if}

				{#if item.action}
					<a class="card-action" href={item.action.href}>{item.action.label}</a>
				{/if}
			</article>
		{/each}
	</div>

	{#if footerAction}
		<a class="footer-link mobile-only" href={footerAction.href}>{footerAction.label}</a>
	{/if}
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
	.area-eyebrow,
	h4,
	.area-description {
		margin: 0;
	}

	.label {
		font-size: 0.88rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #7c3aed;
	}

	h3 {
		font-size: 1.7rem;
		color: #0f172a;
	}

	.description {
		max-width: 60ch;
		font-size: 0.98rem;
		line-height: 1.6;
		color: #475569;
	}

	.area-list {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.area-card {
		padding: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
		display: grid;
		gap: 0.85rem;
	}

	.area-card.complete {
		background: rgba(240, 253, 244, 0.96);
		border-color: rgba(134, 239, 172, 0.7);
	}

	.area-card.pending {
		background: rgba(248, 250, 252, 0.96);
	}

	.area-card.primary {
		box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.08);
	}

	.area-eyebrow {
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: #475569;
	}

	h4 {
		font-size: 1.02rem;
		line-height: 1.35;
		color: #0f172a;
	}

	.area-description {
		font-size: 0.95rem;
		line-height: 1.58;
		color: #475569;
	}

	.meta-row {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.meta-row span {
		padding: 0.35rem 0.65rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.92);
		border: 1px solid rgba(203, 213, 225, 0.8);
		font-size: 0.78rem;
		font-weight: 700;
		color: #334155;
	}

	.card-action,
	.footer-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: fit-content;
		min-height: 44px;
		padding: 0.75rem 0.95rem;
		border-radius: 999px;
		text-decoration: none;
		font-weight: 800;
	}

	.card-action {
		background: rgba(239, 246, 255, 0.92);
		border: 1px solid rgba(147, 197, 253, 0.5);
		color: #0f172a;
	}

	.footer-link {
		background: #1d4ed8;
		color: #ffffff;
	}

	.mobile-only {
		display: none;
	}

	@media (max-width: 900px) {
		.area-list {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 720px) {
		.section-head {
			flex-direction: column;
		}

		.desktop-only {
			display: none;
		}

		.mobile-only {
			display: inline-flex;
		}

		.card-action,
		.footer-link {
			width: 100%;
		}
	}
</style>
