<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { locale, translateText } from '$lib/i18n';
	import { user } from '$lib/stores.js';

	export let title = '';
	export let subtitle = '';
	export let eyebrow = 'Doctor Workspace';
	export let maxWidth = '1260px';

	const navItems = [
		{ href: '/doctor/dashboard', label: 'Dashboard' },
		{ href: '/doctor/patients', label: 'Patients' },
		{ href: '/doctor/analytics', label: 'Analytics' },
		{ href: '/doctor/reports', label: 'Reports' },
		{ href: '/doctor/messages', label: 'Messages' },
		{ href: '/doctor/notifications', label: 'Notifications' }
	];

	function isActive(href) {
		const currentPath = $page.url.pathname;
		if (href === '/doctor/dashboard') {
			return currentPath === href;
		}

		return currentPath === href || currentPath.startsWith(`${href}/`);
	}

	function handleLogout() {
		user.set(null);
		goto('/login');
	}

	function t(text) {
		return translateText(text ?? '', $locale);
	}
</script>

<div class="doctor-shell">
	<div class="doctor-shell__backdrop"></div>
	<div class="doctor-shell__inner" style={`--shell-max-width: ${maxWidth};`}>
		<header class="doctor-shell__header">
			<div class="doctor-shell__brand">
				<p class="doctor-shell__eyebrow">{t(eyebrow)}</p>
				<h1>{t(title)}</h1>
				{#if subtitle}
					<p class="doctor-shell__subtitle">{t(subtitle)}</p>
				{/if}
			</div>
			<div class="doctor-shell__actions">
				<slot name="actions" />
				<button class="doctor-shell__logout" on:click={handleLogout}>{t('Logout')}</button>
			</div>
		</header>

		<nav class="doctor-shell__nav" aria-label={t('Doctor Workspace')}>
			{#each navItems as item}
				<button
					class:active={isActive(item.href)}
					class="doctor-shell__nav-item"
					on:click={() => goto(item.href)}
				>
					{t(item.label)}
				</button>
			{/each}
		</nav>

		<main class="doctor-shell__content">
			<slot />
		</main>
	</div>
</div>

<style>
	:global(body) {
		background: #f5f7fa;
	}

	.doctor-shell {
		position: relative;
		min-height: 100vh;
		padding: 1.75rem;
		background:
			radial-gradient(circle at top left, rgba(79, 70, 229, 0.08), transparent 28%),
			radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 24%),
			linear-gradient(180deg, #f8fafc 0%, #f5f7fa 100%);
	}

	.doctor-shell__backdrop {
		position: absolute;
		inset: 0;
		pointer-events: none;
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.55), rgba(245, 247, 250, 0));
	}

	.doctor-shell__inner {
		position: relative;
		max-width: var(--shell-max-width);
		margin: 0 auto;
	}

	.doctor-shell__header,
	.doctor-shell__nav {
		background: rgba(255, 255, 255, 0.96);
		border: 1px solid #e5e7eb;
		box-shadow: 0 18px 38px rgba(15, 23, 42, 0.06);
	}

	.doctor-shell__header {
		border-radius: 28px;
		padding: 1.5rem 1.65rem;
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.doctor-shell__eyebrow {
		margin: 0 0 0.35rem;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #4f46e5;
	}

	h1 {
		margin: 0;
		font-size: clamp(2rem, 4vw, 2.7rem);
		line-height: 1.05;
		color: #111827;
	}

	.doctor-shell__subtitle {
		margin: 0.55rem 0 0;
		max-width: 760px;
		font-size: 1rem;
		line-height: 1.65;
		color: #4b5563;
	}

	.doctor-shell__actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.doctor-shell__logout,
	.doctor-shell__nav-item {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
		font-weight: 700;
		cursor: pointer;
		transition: 180ms ease;
	}

	.doctor-shell__logout {
		border-radius: 999px;
		padding: 0.82rem 1.15rem;
	}

	.doctor-shell__logout:hover,
	.doctor-shell__nav-item:hover {
		border-color: #c7d2fe;
		background: #eef2ff;
	}

	.doctor-shell__nav {
		border-radius: 22px;
		padding: 0.65rem;
		display: flex;
		gap: 0.55rem;
		flex-wrap: wrap;
		margin-bottom: 1.25rem;
	}

	.doctor-shell__nav-item {
		border-radius: 999px;
		padding: 0.8rem 1rem;
	}

	.doctor-shell__nav-item.active {
		background: #4f46e5;
		border-color: #4f46e5;
		color: #ffffff;
		box-shadow: 0 10px 22px rgba(79, 70, 229, 0.2);
	}

	.doctor-shell__content {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	@media (max-width: 760px) {
		.doctor-shell {
			padding: 1rem;
		}

		.doctor-shell__header {
			border-radius: 22px;
			padding: 1.2rem;
			flex-direction: column;
		}

		.doctor-shell__actions {
			width: 100%;
			justify-content: flex-start;
		}

		.doctor-shell__nav {
			border-radius: 18px;
		}
	}
</style>
