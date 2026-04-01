<script>
	import { onMount } from 'svelte';
	import { formatNumber, locale, translateText } from '$lib/i18n';
	
	export let badges = [];
	
	let visible = false;
	let currentBadgeIndex = 0;
	
	$: currentBadge = badges[currentBadgeIndex];
	$: translatedBadgeName = currentBadge ? translateText(currentBadge.name, $locale) : '';
	$: translatedBadgeDescription = currentBadge
		? translateText(currentBadge.description, $locale)
		: '';
	$: translatedBadgeCount =
		badges.length > 1
			? `${formatNumber(currentBadgeIndex + 1, $locale)} ${translateText('of', $locale)} ${formatNumber(
					badges.length,
					$locale
				)} ${translateText('new badges', $locale)}`
			: '';
	
	onMount(() => {
		if (badges.length > 0) {
			showNextBadge();
		}
	});
	
	function showNextBadge() {
		if (currentBadgeIndex < badges.length) {
			visible = true;
			
			// Hide after 4 seconds and show next badge
			setTimeout(() => {
				visible = false;
				setTimeout(() => {
					currentBadgeIndex++;
					if (currentBadgeIndex < badges.length) {
						showNextBadge();
					}
				}, 500);
			}, 4000);
		}
	}
</script>

{#if currentBadge && visible}
	<div class="badge-notification {visible ? 'show' : ''}">
		<div class="notification-content">
			<div class="badge-header">
				<span class="trophy">🏆</span>
				<h3>{translateText('New Badge Unlocked!', $locale)}</h3>
			</div>
			
			<div class="badge-display">
				<div class="badge-icon">{currentBadge.icon}</div>
				<div class="badge-details">
					<h2>{translatedBadgeName}</h2>
					<p>{translatedBadgeDescription}</p>
				</div>
			</div>
			
			{#if badges.length > 1}
				<div class="badge-count">
					{translatedBadgeCount}
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.badge-notification {
		position: fixed;
		top: 20px;
		right: 20px;
		z-index: 10000;
		max-width: 400px;
		background: white;
		border-radius: 20px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		overflow: hidden;
		transform: translateX(500px);
		opacity: 0;
		transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
	}
	
	.badge-notification.show {
		transform: translateX(0);
		opacity: 1;
	}
	
	.notification-content {
		padding: 1.5rem;
		background: linear-gradient(135deg, #fff9e6 0%, #ffe6f0 100%);
		border: 3px solid #ffd700;
	}
	
	.badge-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}
	
	.trophy {
		font-size: 2rem;
		animation: bounce 0.6s ease infinite;
	}
	
	@keyframes bounce {
		0%, 100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-10px);
		}
	}
	
	.badge-header h3 {
		margin: 0;
		color: #333;
		font-size: 1.2rem;
	}
	
	.badge-display {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 1rem;
		background: white;
		border-radius: 15px;
		margin-bottom: 1rem;
	}
	
	.badge-icon {
		font-size: 4rem;
		animation: celebrate 0.8s ease;
	}
	
	@keyframes celebrate {
		0% {
			transform: scale(0) rotate(0deg);
		}
		50% {
			transform: scale(1.2) rotate(180deg);
		}
		100% {
			transform: scale(1) rotate(360deg);
		}
	}
	
	.badge-details h2 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 1.3rem;
	}
	
	.badge-details p {
		margin: 0;
		color: #666;
		font-size: 0.95rem;
		line-height: 1.4;
	}
	
	.badge-count {
		text-align: center;
		color: #999;
		font-size: 0.85rem;
		font-weight: 600;
	}
	
	@media (max-width: 480px) {
		.badge-notification {
			top: 10px;
			right: 10px;
			left: 10px;
			max-width: none;
		}
		
		.badge-display {
			flex-direction: column;
			text-align: center;
		}
		
		.badge-icon {
			font-size: 3rem;
		}
		
		.badge-details h2 {
			font-size: 1.1rem;
		}
	}
</style>
