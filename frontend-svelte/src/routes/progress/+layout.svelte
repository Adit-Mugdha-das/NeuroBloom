<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { user } from '$lib/stores';

	let currentUser = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	const tabs = [
		{ href: '/progress', label: 'Overview' },
		{ href: '/progress/domains', label: 'Domain Performance' },
		{ href: '/progress/history', label: 'Training History' },
		{ href: '/progress/achievements', label: 'Achievements' }
	];

	function isActive(href) {
		return href === '/progress' ? page.url.pathname === href : page.url.pathname.startsWith(href);
	}
</script>

<div class="progress-shell">
	<header class="progress-header">
		<div class="header-copy">
			<p class="eyebrow">NeuroBloom Progress</p>
			<h1>Your Progress Area</h1>
			<p class="header-subcopy">Each view focuses on one purpose only, so reviewing progress stays calm and easy to follow.</p>
		</div>
		<div class="header-actions">
			{#if currentUser}
				<span class="user-email">{currentUser.email}</span>
			{/if}
			<button class="back-btn" on:click={() => goto('/dashboard')}>Back to Dashboard</button>
		</div>
	</header>

	<nav class="progress-nav" aria-label="Progress sections">
		{#each tabs as tab}
			<a href={tab.href} class:selected={isActive(tab.href)}>{tab.label}</a>
		{/each}
	</nav>

	<div class="progress-content">
		<slot />
	</div>
</div>

<style>
	:global(body) {
		background: linear-gradient(135deg, #eef2ff, #e0f2fe);
	}

	.progress-shell {
		min-height: 100vh;
		padding: 1.5rem;
		background:
			radial-gradient(circle at top left, rgba(79, 70, 229, 0.12), transparent 28%),
			radial-gradient(circle at right top, rgba(34, 211, 238, 0.12), transparent 24%),
			linear-gradient(135deg, #eef2ff, #e0f2fe);
		color: #1f2937;
	}

	.progress-header,
	.progress-nav,
	.progress-content :global(.progress-panel) {
		max-width: 1180px;
		margin-left: auto;
		margin-right: auto;
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		padding: 1.3rem 1.4rem;
		margin-bottom: 0.9rem;
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	}

	.eyebrow {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #4f46e5;
	}

	.header-copy h1 {
		margin: 0.2rem 0 0.35rem;
		font-size: 2rem;
		color: #111827;
	}

	.header-subcopy {
		margin: 0;
		max-width: 720px;
		line-height: 1.55;
		color: #64748b;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.user-email {
		font-size: 0.84rem;
		color: #64748b;
	}

	.back-btn {
		border: none;
		border-radius: 999px;
		padding: 0.8rem 1.15rem;
		font-weight: 700;
		cursor: pointer;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: #ffffff;
		box-shadow: 0 10px 24px rgba(79, 70, 229, 0.18);
	}

	.progress-nav {
		display: flex;
		gap: 0.7rem;
		padding: 0.4rem;
		margin-bottom: 1rem;
		background: rgba(248, 250, 252, 0.7);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.68);
		border-radius: 18px;
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
		overflow-x: auto;
	}

	.progress-nav a {
		text-decoration: none;
		padding: 0.85rem 1.1rem;
		border-radius: 14px;
		font-weight: 700;
		white-space: nowrap;
		color: #475569;
	}

	.progress-nav a.selected {
		background: rgba(79, 70, 229, 0.12);
		color: #4338ca;
		box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.12);
	}

	.progress-content {
		display: grid;
		gap: 1rem;
	}

	@media (max-width: 860px) {
		.progress-shell {
			padding: 1rem;
		}

		.progress-header {
			flex-direction: column;
		}

		.header-actions {
			justify-content: flex-start;
		}
	}
</style>