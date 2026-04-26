<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { formatNumber, locale, localeText } from '$lib/i18n';
	import { getPatientBadgeCopy } from '$lib/patient-copy.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let badgeData = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);
	const n = (value) => formatNumber(value, $locale);

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
			error = lt('Complete more training sessions to unlock achievements.', 'অর্জন দেখতে আরও কিছু ট্রেনিং সেশন সম্পন্ন করুন।');
		} finally {
			loading = false;
		}
	}

	function formatDate(dateValue) {
		return new Date(dateValue).toLocaleDateString($locale === 'bn' ? 'bn-BD' : 'en-US');
	}

	function getBadgeDisplay(badge) {
		return getPatientBadgeCopy(badge?.badge_id || badge?.id, $locale);
	}
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
			<p>{lt('Loading achievements...', 'অর্জন লোড হচ্ছে...')}</p>
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>{lt('Achievements unavailable', 'অর্জন পাওয়া যাচ্ছে না')}</h2>
			<p>{error}</p>
		</section>
	{:else if badgeData}
		<div class="achievement-panel">
			<div class="glass-card achievement-header">
				<div class="header-copy">
					<p class="card-label">{lt('Achievements', 'অর্জন')}</p>
					<h2>{badgeData.earned_count} {lt('of', 'মধ্যে')} {badgeData.total_badges} {lt('earned', 'অর্জিত')}</h2>
				</div>
				<p class="achievement-copy">{lt('A separate view for badges keeps the main progress area focused on recovery and training.', 'ব্যাজের জন্য আলাদা ভিউ থাকায় মূল প্রগ্রেস এলাকা রিকভারি ও ট্রেনিংয়েই কেন্দ্রীভূত থাকে।')}</p>
			</div>

			<div class="glass-card badge-section">
				<div class="achievement-grid">
					{#each badgeData.all_badges as badge}
						{@const badgeCopy = getBadgeDisplay(badge)}
						<article class="badge-card {badge.earned ? 'earned' : 'locked'}">
							<div class="badge-icon">{badge.icon}</div>
							<p class="badge-name">{badgeCopy.name}</p>
							<p class="badge-description">{badgeCopy.description}</p>
							{#if badge.earned}
								<p class="badge-status earned-status">{lt('Earned', 'অর্জিত')} {formatDate(badge.earned_at)}</p>
							{:else}
								<p class="badge-status locked-status">{lt('Locked', 'লকড')}</p>
							{/if}
						</article>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.progress-panel {
	width: 100%;
	max-width: none;
}

.glass-card,
.state-panel {
	background: rgba(248, 250, 252, 0.84);
	backdrop-filter: blur(10px);
	border: 1px solid rgba(255, 255, 255, 0.72);
	border-radius: 22px;
	padding: 1.25rem;
	box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	box-sizing: border-box;
}

.achievement-panel {
	width: 100%;
	max-width: none;
	margin: 0;
	display: grid;
	grid-template-columns: minmax(0, 1fr);
	gap: 0.75rem;
}

.achievement-header,
.badge-section,
.state-panel {
	width: 100%;
	box-sizing: border-box;
}

.achievement-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 1rem;
	background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(79, 70, 229, 0.04) 100%);
	border-color: rgba(99, 102, 241, 0.22);
}

.header-copy {
	min-width: 0;
}

.card-label {
	margin: 0;
	font-size: 0.78rem;
	text-transform: uppercase;
	letter-spacing: 0.08em;
	font-weight: 800;
	color: #4f46e5;
}

.achievement-header h2,
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
	font-size: 0.9rem;
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

@media (max-width: 860px) {
	.achievement-header {
		flex-direction: column;
		align-items: flex-start;
	}
}

@media (max-width: 960px) {
	.achievement-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}
}

@media (max-width: 640px) {
	.achievement-grid {
		grid-template-columns: 1fr;
	}
}
</style>
