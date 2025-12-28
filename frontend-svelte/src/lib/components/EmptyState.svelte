<script>
	export let icon = '🧠';
	export let title = 'No Data Yet';
	export let message = 'Get started to see your progress here.';
	export let actionText = 'Get Started';
	export let actionLink = '/training';
	export let tip = '';
	export let variant = 'default'; // default, compact, large
</script>

<div class="empty-state {variant}">
	<div class="empty-content">
		<div class="empty-icon">{icon}</div>
		<h3 class="empty-title">{title}</h3>
		<p class="empty-message">{message}</p>
		
		{#if actionText && actionLink}
			<a href={actionLink} class="empty-action">
				{actionText} →
			</a>
		{/if}
		
		{#if tip}
			<div class="empty-tip">
				<span class="tip-icon">💡</span>
				<span class="tip-text">{tip}</span>
			</div>
		{/if}
	</div>
</div>

<style>
	.empty-state {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 3rem 2rem;
		min-height: 300px;
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		border-radius: 20px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
		animation: fadeIn 0.5s ease;
	}
	
	.empty-state.compact {
		min-height: 200px;
		padding: 2rem 1.5rem;
	}
	
	.empty-state.large {
		min-height: 400px;
		padding: 4rem 2rem;
	}
	
	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.empty-content {
		text-align: center;
		max-width: 500px;
	}
	
	.empty-icon {
		font-size: 5rem;
		margin-bottom: 1.5rem;
		animation: bounce 2s ease-in-out infinite;
	}
	
	@keyframes bounce {
		0%, 100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-15px);
		}
	}
	
	.empty-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: #2d3748;
		margin: 0 0 1rem 0;
	}
	
	.empty-message {
		font-size: 1.1rem;
		color: #4a5568;
		margin: 0 0 2rem 0;
		line-height: 1.6;
	}
	
	.empty-action {
		display: inline-block;
		padding: 0.875rem 2rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		text-decoration: none;
		border-radius: 10px;
		font-weight: 600;
		font-size: 1rem;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
	}
	
	.empty-action:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
	}
	
	.empty-tip {
		margin-top: 2rem;
		padding: 1rem 1.5rem;
		background: rgba(255, 255, 255, 0.7);
		border-radius: 10px;
		display: inline-flex;
		align-items: center;
		gap: 0.75rem;
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.5);
	}
	
	.tip-icon {
		font-size: 1.25rem;
	}
	
	.tip-text {
		font-size: 0.9rem;
		color: #2d3748;
		font-weight: 500;
	}
	
	@media (max-width: 768px) {
		.empty-state {
			padding: 2rem 1rem;
			min-height: 250px;
		}
		
		.empty-icon {
			font-size: 3.5rem;
		}
		
		.empty-title {
			font-size: 1.5rem;
		}
		
		.empty-message {
			font-size: 1rem;
		}
	}
</style>
