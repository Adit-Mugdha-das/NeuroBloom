<script>
	export let label = '';
	export let title = '';
	export let items = [];
	export let disclosureLabel = '';
	export let open = false;
</script>

<section class="section-card">
	<p class="label">{label}</p>
	<h3>{title}</h3>

	<div class="summary-list">
		{#each items.slice(0, 3) as item}
			<div class="summary-item">
				<div class="summary-copy">
					<p class="item-label">{item.label}</p>
					<p class="item-value">{item.value}</p>
					<p class="item-note">{item.note}</p>
				</div>
				{#if item.action}
					<a class="item-action" href={item.action.href}>{item.action.label}</a>
				{/if}
			</div>
		{/each}
	</div>

	<details class="details" bind:open>
		<summary>{disclosureLabel}</summary>
		{#if open}
			<div class="details-body">
				<slot />
			</div>
		{/if}
	</details>
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
		color: #0f766e;
	}

	h3 {
		margin: 0.4rem 0 0;
		font-size: 1.7rem;
		color: #0f172a;
	}

	.summary-list {
		margin-top: 1rem;
		display: grid;
		gap: 0.85rem;
	}

	.summary-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
	}

	.summary-copy {
		display: grid;
		gap: 0.2rem;
	}

	.item-label,
	.item-value,
	.item-note {
		margin: 0;
	}

	.item-label {
		font-size: 0.92rem;
		font-weight: 700;
		color: #64748b;
	}

	.item-value {
		font-size: 1.08rem;
		font-weight: 800;
		color: #0f172a;
	}

	.item-note {
		font-size: 0.95rem;
		line-height: 1.55;
		color: #475569;
	}

	.item-action {
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 46px;
		padding: 0.8rem 1rem;
		border-radius: 999px;
		background: #ffffff;
		border: 1px solid rgba(148, 163, 184, 0.8);
		color: #0f172a;
		text-decoration: none;
		font-weight: 800;
	}

	.details {
		margin-top: 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
		overflow: hidden;
	}

	.details summary {
		cursor: pointer;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 800;
		color: #0f172a;
		list-style: none;
	}

	.details summary::-webkit-details-marker {
		display: none;
	}

	.details-body {
		padding: 0 1rem 1rem;
	}

	@media (max-width: 720px) {
		.summary-item {
			flex-direction: column;
			align-items: stretch;
		}

		.item-action {
			width: 100%;
		}
	}
</style>
