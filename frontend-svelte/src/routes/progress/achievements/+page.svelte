<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let badgeData = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadAchievements();
	});

	async function loadAchievements() {
		loading = true;
		error = null;

		try {
			badgeData = await training.getAvailableBadges(currentUser.id);
		} catch (loadError) {
			console.error('Error loading achievements:', loadError);
			error = 'Complete more training sessions to unlock achievements.';
		} finally {
			loading = false;
		}
	}

	function formatDate(dateValue) {
		return new Date(dateValue).toLocaleDateString();
	}
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
			<p>Loading achievements...</p>
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>Achievements unavailable</h2>
			<p>{error}</p>
		</section>
	{:else if badgeData}
		<section class="glass-card achievement-shell">
			<div class="achievement-head">
				<div>
					<p class="card-label">Achievements</p>
					<h2>{badgeData.earned_count} of {badgeData.total_badges} earned</h2>
				</div>
				<p class="achievement-copy">A separate view for badges keeps the main progress area focused on recovery and training.</p>
			</div>

			<div class="achievement-grid">
				{#each badgeData.all_badges as badge}
					<article class="badge-card {badge.earned ? 'earned' : 'locked'}">
						<div class="badge-icon">{badge.icon}</div>
						<p class="badge-name">{badge.name}</p>
						<p class="badge-description">{badge.description}</p>
						{#if badge.earned}
							<p class="badge-status earned-status">Earned {formatDate(badge.earned_at)}</p>
						{:else}
							<p class="badge-status locked-status">Locked</p>
						{/if}
					</article>
				{/each}
			</div>
		</section>
	{/if}
</div>

<style>
	.glass-card,
	.state-panel {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	}

	.achievement-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-end;
		margin-bottom: 1rem;
	}

	.card-label {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #4f46e5;
	}

	.achievement-head h2,
	.state-panel h2 {
		margin: 0.25rem 0 0;
		font-size: 1.7rem;
		color: #111827;
	}

	.achievement-copy,
	.state-panel p {
		margin: 0;
		line-height: 1.55;
		color: #64748b;
	}

	.achievement-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1rem;
	}

	.badge-card {
		padding: 1rem;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.72);
		border: 1px solid rgba(255, 255, 255, 0.8);
		text-align: center;
	}

	.badge-card.earned {
		box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.12), 0 10px 24px rgba(245, 158, 11, 0.08);
	}

	.badge-card.locked {
		opacity: 0.72;
	}

	.badge-icon {
		font-size: 3rem;
		margin-bottom: 0.6rem;
	}

	.badge-name {
		margin: 0;
		font-size: 1rem;
		font-weight: 700;
		color: #111827;
	}

	.badge-description {
		margin: 0.45rem 0 0;
		color: #64748b;
		line-height: 1.5;
		font-size: 0.9rem;
	}

	.badge-status {
		margin: 0.75rem 0 0;
		font-size: 0.8rem;
		font-weight: 700;
	}

	.earned-status {
		color: #b45309;
	}

	.locked-status {
		color: #64748b;
	}

	@media (max-width: 960px) {
		.achievement-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 640px) {
		.achievement-head {
			flex-direction: column;
			align-items: flex-start;
		}

		.achievement-grid {
			grid-template-columns: 1fr;
		}
	}
</style>