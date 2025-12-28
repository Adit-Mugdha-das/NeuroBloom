<script>
	export let variant = 'default'; // default, card, list
	export let count = 1;
</script>

<div class="skeleton-container {variant}">
	{#each Array(count) as _, i}
		{#if variant === 'card'}
			<div class="skeleton-card">
				<div class="skeleton skeleton-circle"></div>
				<div class="skeleton skeleton-text"></div>
				<div class="skeleton skeleton-text short"></div>
			</div>
		{:else if variant === 'list'}
			<div class="skeleton-list-item">
				<div class="skeleton skeleton-avatar"></div>
				<div class="skeleton-content">
					<div class="skeleton skeleton-text"></div>
					<div class="skeleton skeleton-text short"></div>
				</div>
			</div>
		{:else}
			<div class="skeleton skeleton-block"></div>
		{/if}
	{/each}
</div>

<style>
	.skeleton-container {
		width: 100%;
	}
	
	.skeleton {
		background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
		background-size: 200% 100%;
		animation: loading 1.5s ease-in-out infinite;
		border-radius: 8px;
	}
	
	@keyframes loading {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}
	
	.skeleton-block {
		height: 200px;
		width: 100%;
	}
	
	.skeleton-card {
		background: white;
		border-radius: 15px;
		padding: 1.5rem;
		box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
		margin-bottom: 1rem;
	}
	
	.skeleton-circle {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		margin: 0 auto 1rem auto;
	}
	
	.skeleton-text {
		height: 20px;
		margin-bottom: 0.75rem;
	}
	
	.skeleton-text.short {
		width: 60%;
		margin: 0 auto;
	}
	
	.skeleton-list-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		background: white;
		border-radius: 10px;
		margin-bottom: 0.75rem;
	}
	
	.skeleton-avatar {
		width: 50px;
		height: 50px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.skeleton-content {
		flex: 1;
	}
	
	.skeleton-container.card {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	.skeleton-container.list {
		display: flex;
		flex-direction: column;
	}
</style>
