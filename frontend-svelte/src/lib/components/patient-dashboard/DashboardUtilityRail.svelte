<script>
	export let label = '';
	export let title = '';
	export let items = [];
	export let detailsLabel = '';
	export let detailsOpen = false;
</script>

<section class="rail-panel">
	<p class="label">{label}</p>
	<h2>{title}</h2>

	<div class="rail-list">
		{#each items as item}
			<article class="rail-card">
				<div class="rail-copy">
					<p class="item-label">{item.label}</p>
					<p class="item-value">{item.value}</p>
					{#if item.note}
						<p class="item-note">{item.note}</p>
					{/if}
				</div>
				{#if item.action}
					<a class="item-action" href={item.action.href}>
						{item.action.label}
						{#if item.action.badge}
							<span class="action-badge">{item.action.badge}</span>
						{/if}
					</a>
				{/if}
			</article>
		{/each}
	</div>

	{#if detailsLabel}
		<details class="rail-details" bind:open={detailsOpen}>
			<summary>{detailsLabel}</summary>
			{#if detailsOpen}
				<div class="rail-details__body">
					<slot />
				</div>
			{/if}
		</details>
	{/if}
</section>

<style>
	.rail-panel {
		padding: 1.25rem;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.86);
		border: 1px solid rgba(203, 213, 225, 0.82);
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.05);
		display: grid;
		gap: 1rem;
	}

	.label,
	h2,
	.item-label,
	.item-value,
	.item-note {
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
		font-size: 1.45rem;
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
		gap: 0.8rem;
	}

	.rail-copy {
		display: grid;
		gap: 0.28rem;
	}

	.item-label {
		font-size: 0.88rem;
		font-weight: 700;
		color: #64748b;
	}

	.item-value {
		font-size: 1.08rem;
		font-weight: 800;
		color: #0f172a;
	}

	.item-note {
		font-size: 0.94rem;
		line-height: 1.5;
		color: #475569;
	}

	.item-action {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.45rem;
		min-height: 44px;
		padding: 0.75rem 0.95rem;
		border-radius: 999px;
		background: #ffffff;
		border: 1px solid rgba(148, 163, 184, 0.75);
		color: #0f172a;
		text-decoration: none;
		font-weight: 800;
	}

	.action-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.45rem;
		height: 1.45rem;
		padding: 0 0.35rem;
		border-radius: 999px;
		background: #1d4ed8;
		color: #ffffff;
		font-size: 0.76rem;
	}

	.rail-details {
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.82);
		overflow: hidden;
	}

	.rail-details summary {
		padding: 1rem;
		cursor: pointer;
		list-style: none;
		font-size: 0.98rem;
		font-weight: 800;
		color: #0f172a;
	}

	.rail-details summary::-webkit-details-marker {
		display: none;
	}

	.rail-details__body {
		padding: 0 1rem 1rem;
	}
</style>
