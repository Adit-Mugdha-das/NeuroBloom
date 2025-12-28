<script>
	import EmptyState from './EmptyState.svelte';
	
	export let badges = [];
	export let totalBadges = 0;
	export let earnedCount = 0;
	
	let selectedCategory = 'all';
	
	const categories = {
		all: { name: 'All Badges', icon: '🏆' },
		getting_started: { name: 'Getting Started', icon: '🎯' },
		milestone: { name: 'Milestones', icon: '🏔️' },
		streak: { name: 'Streaks', icon: '🔥' },
		performance: { name: 'Performance', icon: '💯' },
		mastery: { name: 'Mastery', icon: '🎓' },
		speed: { name: 'Speed', icon: '⚡' },
		improvement: { name: 'Improvement', icon: '📈' }
	};
	
	$: filteredBadges = selectedCategory === 'all' 
		? badges 
		: badges.filter(b => b.category === selectedCategory);
	
	$: progressPercentage = totalBadges > 0 ? (earnedCount / totalBadges * 100) : 0;
	
	function formatDate(dateStr) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { 
			month: 'short', 
			day: 'numeric',
			year: 'numeric'
		});
	}
</script>

<div class="badges-section">
	<div class="badges-header">
		<div class="header-left">
			<h2>🏆 Achievement Badges</h2>
			<p class="subtitle">Unlock badges by completing milestones and challenges</p>
		</div>
		<div class="badge-stats">
			<div class="stat">
				<span class="stat-number">{earnedCount}</span>
				<span class="stat-label">/ {totalBadges} Earned</span>
			</div>
			<div class="progress-ring">
				<svg width="80" height="80">
					<circle cx="40" cy="40" r="35" class="progress-ring-bg" />
					<circle 
						cx="40" 
						cy="40" 
						r="35" 
						class="progress-ring-fill"
						style="stroke-dasharray: {2 * Math.PI * 35}; stroke-dashoffset: {2 * Math.PI * 35 * (1 - progressPercentage / 100)}"
					/>
					<text x="40" y="45" text-anchor="middle" class="progress-text">{progressPercentage.toFixed(1)}%</text>
				</svg>
			</div>
		</div>
	</div>
	
	<!-- Category Filter -->
	<div class="category-filter">
		{#each Object.entries(categories) as [key, category]}
			<button 
				class="category-btn {selectedCategory === key ? 'active' : ''}"
				on:click={() => selectedCategory = key}
			>
				<span class="cat-icon">{category.icon}</span>
				<span class="cat-name">{category.name}</span>
			</button>
		{/each}
	</div>
	
	<!-- Badges Grid -->
	<div class="badges-grid">
		{#each filteredBadges as badge}
			<div class="badge-card {badge.earned ? 'earned' : 'locked'}">
				<div class="badge-icon {badge.earned ? 'earned-icon' : 'locked-icon'}">
					{badge.icon}
				</div>
				<div class="badge-info">
					<h3 class="badge-name">{badge.name}</h3>
					<p class="badge-description">{badge.description}</p>
					{#if badge.earned}
						<div class="earned-date">
							<span class="checkmark">✓</span>
							Earned {formatDate(badge.earned_at)}
						</div>
					{:else}
						<div class="locked-label">
							<span class="lock-icon">🔒</span>
							Locked
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>
	
	{#if filteredBadges.length === 0}
		<div style="margin: 2rem 0;">
			<EmptyState 
				icon="🎯"
				title={selectedCategory === 'all' ? 'Start Earning Badges!' : 'No Badges in This Category'}
				message={selectedCategory === 'all' ? 'Complete training sessions to unlock your first achievement badge!' : 'Try other categories or complete more sessions to unlock badges here.'}
				actionText="Start Training"
				actionLink="/training"
				tip="Badges track your progress, consistency, and mastery across all cognitive domains"
				variant="compact"
			/>
		</div>
	{/if}
</div>

<style>
	.badges-section {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.badges-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1.5rem;
		border-bottom: 2px solid #f0f0f0;
	}
	
	.header-left h2 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 1.8rem;
	}
	
	.subtitle {
		margin: 0;
		color: #666;
		font-size: 0.95rem;
	}
	
	.badge-stats {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.stat {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}
	
	.stat-number {
		font-size: 2rem;
		font-weight: 700;
		color: #667eea;
	}
	
	.stat-label {
		font-size: 0.9rem;
		color: #666;
	}
	
	.progress-ring {
		position: relative;
	}
	
	.progress-ring-bg {
		fill: none;
		stroke: #f0f0f0;
		stroke-width: 6;
	}
	
	.progress-ring-fill {
		fill: none;
		stroke: #667eea;
		stroke-width: 6;
		stroke-linecap: round;
		transform: rotate(-90deg);
		transform-origin: 50% 50%;
		transition: stroke-dashoffset 0.5s ease;
	}
	
	.progress-text {
		font-size: 1rem;
		font-weight: 700;
		fill: #333;
	}
	
	.category-filter {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}
	
	.category-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.25rem;
		border: 2px solid #e0e0e0;
		border-radius: 25px;
		background: white;
		color: #666;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.category-btn:hover {
		border-color: #667eea;
		color: #667eea;
		transform: translateY(-2px);
	}
	
	.category-btn.active {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border-color: #667eea;
		color: white;
	}
	
	.cat-icon {
		font-size: 1.2rem;
	}
	
	.badges-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1.5rem;
	}
	
	.badge-card {
		background: #f8f9fa;
		border-radius: 15px;
		padding: 1.5rem;
		transition: all 0.3s;
		border: 2px solid transparent;
	}
	
	.badge-card.earned {
		background: linear-gradient(135deg, #fff9e6 0%, #ffe6f0 100%);
		border-color: #ffd700;
	}
	
	.badge-card.earned:hover {
		transform: translateY(-5px);
		box-shadow: 0 8px 20px rgba(255, 215, 0, 0.3);
	}
	
	.badge-card.locked {
		opacity: 0.6;
	}
	
	.badge-card.locked:hover {
		opacity: 0.8;
	}
	
	.badge-icon {
		font-size: 4rem;
		text-align: center;
		margin-bottom: 1rem;
	}
	
	.earned-icon {
		animation: bounce 0.6s ease;
	}
	
	.locked-icon {
		filter: grayscale(1);
		opacity: 0.5;
	}
	
	@keyframes bounce {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.1); }
	}
	
	.badge-info {
		text-align: center;
	}
	
	.badge-name {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 1.1rem;
	}
	
	.badge-description {
		margin: 0 0 0.75rem 0;
		color: #666;
		font-size: 0.9rem;
		line-height: 1.4;
	}
	
	.earned-date {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		color: #4caf50;
		font-size: 0.85rem;
		font-weight: 600;
	}
	
	.checkmark {
		background: #4caf50;
		color: white;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
	}
	
	.locked-label {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		color: #999;
		font-size: 0.85rem;
		font-weight: 600;
	}
	
	.lock-icon {
		font-size: 1rem;
	}
	
	.empty-state {
		text-align: center;
		padding: 4rem 2rem;
		color: #999;
	}
	
	.empty-icon {
		font-size: 4rem;
		margin-bottom: 1rem;
		opacity: 0.5;
	}
	
	.empty-state p {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
		font-weight: 600;
	}
	
	.empty-state small {
		font-size: 0.9rem;
	}
	
	@media (max-width: 768px) {
		.badges-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 1.5rem;
		}
		
		.badge-stats {
			align-self: stretch;
			justify-content: space-between;
		}
		
		.badges-grid {
			grid-template-columns: 1fr;
		}
		
		.category-filter {
			gap: 0.5rem;
		}
		
		.category-btn {
			padding: 0.5rem 1rem;
			font-size: 0.85rem;
		}
	}
</style>
