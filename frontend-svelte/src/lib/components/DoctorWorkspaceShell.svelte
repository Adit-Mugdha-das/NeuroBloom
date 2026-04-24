<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { locale, localeText } from '$lib/i18n/runtime.js';
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
	const shellCopy = {
		'Doctor Workspace': { en: 'Doctor Workspace', bn: 'ডাক্তার ওয়ার্কস্পেস' },
		Logout: { en: 'Logout', bn: 'লগ আউট' },
		Dashboard: { en: 'Dashboard', bn: 'ড্যাশবোর্ড' },
		Patients: { en: 'Patients', bn: 'রোগী' },
		Analytics: { en: 'Analytics', bn: 'অ্যানালিটিক্স' },
		Reports: { en: 'Reports', bn: 'রিপোর্ট' },
		Messages: { en: 'Messages', bn: 'বার্তা' },
		Notifications: { en: 'Notifications', bn: 'নোটিফিকেশন' }
	};

	// ── Settings dropdown state ──
	let settingsOpen = false;
	let profileName = '';
	let profileEmail = '';
	let profileSpecialty = '';
	let profileSaved = false;

	$: if (settingsOpen) {
		profileName     = $user?.full_name ?? $user?.name ?? '';
		profileEmail    = $user?.email ?? '';
		profileSpecialty = $user?.specialty ?? '';
		profileSaved    = false;
	}

	function toggleSettings() {
		settingsOpen = !settingsOpen;
	}

	function closeSettings() {
		settingsOpen = false;
	}

	function saveProfile() {
		user.update((u) => ({
			...u,
			full_name: profileName,
			name: profileName,
			email: profileEmail,
			specialty: profileSpecialty
		}));
		profileSaved = true;
		setTimeout(() => { profileSaved = false; }, 2200);
	}

	function handleLanguageChange(e) {
		setLocale(e.currentTarget.value);
	}

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
		return localeText(shellCopy[text] ?? text ?? '', $locale);
	}
</script>

<div class="doctor-shell">

	<!-- ── Full-width sticky navbar ── -->
	<nav class="doctor-shell__topbar" aria-label={t('Doctor Workspace')}>
		<div class="doctor-shell__topbar-inner">

			<div class="doctor-shell__brand">
				<span class="doctor-shell__logo">NB</span>
				<div>
					<p class="doctor-shell__brand-name">NeuroBloom</p>
					<p class="doctor-shell__brand-role">Doctor Portal</p>
				</div>
			</div>

			<div class="doctor-shell__nav-items">
				{#each navItems as item}
					<button
						class:active={isActive(item.href)}
						class="doctor-shell__nav-item"
						on:click={() => goto(item.href)}
					>
						{t(item.label)}
					</button>
				{/each}
			</div>

			<div class="doctor-shell__nav-right">
				<slot name="actions" />

				<!-- Settings button + dropdown -->
				<div class="settings-wrapper">
					<button
						class="doctor-shell__settings-btn"
						class:active={settingsOpen}
						on:click={toggleSettings}
						aria-haspopup="dialog"
						aria-expanded={settingsOpen}
					>
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="15" height="15" aria-hidden="true">
							<path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/>
						</svg>
						{t('Settings')}
					</button>

					{#if settingsOpen}
						<!-- click-outside backdrop -->
						<!-- svelte-ignore a11y-click-events-have-key-events -->
						<!-- svelte-ignore a11y-no-static-element-interactions -->
						<div class="settings-backdrop" on:click={closeSettings}></div>

						<div class="settings-panel" role="dialog" aria-label={t('Settings')}>

							<!-- ── Doctor profile section ── -->
							<div class="settings-section">
								<p class="settings-kicker">{t('Your Profile')}</p>
								<p class="settings-section-desc">{t('Edit your display name, email, and specialty.')}</p>

								<label class="settings-field">
									<span>{t('Full name')}</span>
									<input type="text" bind:value={profileName} placeholder="Dr. Jane Smith" />
								</label>

								<label class="settings-field">
									<span>{t('Email')}</span>
									<input type="email" bind:value={profileEmail} placeholder="doctor@hospital.org" />
								</label>

								<label class="settings-field">
									<span>{t('Specialty')}</span>
									<input type="text" bind:value={profileSpecialty} placeholder="e.g. Neurology" />
								</label>

								<button
									class="settings-save-btn"
									class:saved={profileSaved}
									on:click={saveProfile}
								>
									{#if profileSaved}
										<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="14" height="14" aria-hidden="true"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
										{t('Saved!')}
									{:else}
										{t('Save Changes')}
									{/if}
								</button>
							</div>

							<div class="settings-divider"></div>

							<!-- ── Language section ── -->
							<div class="settings-section">
								<p class="settings-kicker">{t('Language')}</p>
								<p class="settings-section-desc">{t('Choose the language used across the NeuroBloom interface.')}</p>

								<label class="settings-field">
									<span>{t('Interface language')}</span>
									<select data-localize-skip value={$locale} on:change={handleLanguageChange}>
										<option value="en">English</option>
										<option value="bn">বাংলা (Bengali)</option>
									</select>
								</label>
							</div>

						</div>
					{/if}
				</div>

				<button class="doctor-shell__logout" on:click={handleLogout}>{t('Logout')}</button>
			</div>

		</div>
	</nav>

	<!-- ── Page body ── -->
	<div class="doctor-shell__body" style={`--shell-max-width: ${maxWidth};`}>

		<!-- Page title strip -->
		<header class="doctor-shell__page-header">
			<div class="doctor-shell__page-header-inner">
				<p class="doctor-shell__eyebrow">{t(eyebrow)}</p>
				<h1>{t(title)}</h1>
				{#if subtitle}
					<p class="doctor-shell__subtitle">{t(subtitle)}</p>
				{/if}
			</div>
		</header>

		<!-- Content card -->
		<div class="doctor-shell__card">
			<main class="doctor-shell__content">
				<slot />
			</main>
		</div>

	</div>
</div>

<style>
	/* ── Global ── */
	:global(body) {
		margin: 0;
		background: #eef2ff;
	}

	/* ── Page shell ── */
	.doctor-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background:
			radial-gradient(ellipse 80% 40% at 10% -10%, rgba(99, 102, 241, 0.14) 0%, transparent 60%),
			radial-gradient(ellipse 70% 35% at 90% 5%,  rgba(59, 130, 246, 0.12) 0%, transparent 55%),
			linear-gradient(165deg, #dbeafe 0%, #e0e7ff 30%, #eff6ff 65%, #f0f4ff 100%);
	}

	/* ══════════════════════════════════════
	   NAVBAR — full-width, sticky, polished
	══════════════════════════════════════ */
	.doctor-shell__topbar {
		position: sticky;
		top: 0;
		z-index: 100;
		width: 100%;
		background: rgba(255, 255, 255, 0.96);
		backdrop-filter: blur(20px);
		-webkit-backdrop-filter: blur(20px);
		border-bottom: 1px solid rgba(99, 102, 241, 0.13);
		box-shadow:
			0 1px 0 rgba(255, 255, 255, 0.9) inset,
			0 4px 28px rgba(30, 27, 75, 0.09);
	}

	.doctor-shell__topbar-inner {
		max-width: 1380px;
		margin: 0 auto;
		padding: 0 2rem;
		height: 64px;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	/* Brand */
	.doctor-shell__brand {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		padding-right: 1.5rem;
		border-right: 1px solid #e5e7eb;
		margin-right: 0.25rem;
		flex-shrink: 0;
	}

	.doctor-shell__logo {
		width: 34px;
		height: 34px;
		border-radius: 9px;
		background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
		color: #fff;
		font-size: 0.72rem;
		font-weight: 900;
		display: flex;
		align-items: center;
		justify-content: center;
		letter-spacing: 0.04em;
		flex-shrink: 0;
		box-shadow: 0 4px 10px rgba(99, 102, 241, 0.35);
	}

	.doctor-shell__brand-name {
		margin: 0;
		font-size: 0.92rem;
		font-weight: 800;
		color: #1e3a8a;
		line-height: 1.1;
		white-space: nowrap;
	}

	.doctor-shell__brand-role {
		margin: 0;
		font-size: 0.63rem;
		font-weight: 700;
		color: #818cf8;
		letter-spacing: 0.07em;
		text-transform: uppercase;
	}

	/* Nav links */
	.doctor-shell__nav-items {
		display: flex;
		align-items: center;
		gap: 0.1rem;
		flex: 1;
	}

	.doctor-shell__nav-item {
		border: none;
		background: transparent;
		color: #4b5563;
		font-size: 0.85rem;
		font-weight: 600;
		padding: 0.45rem 0.9rem;
		border-radius: 7px;
		cursor: pointer;
		transition: background 130ms ease, color 130ms ease;
		white-space: nowrap;
		line-height: 1;
	}

	.doctor-shell__nav-item:hover {
		background: rgba(99, 102, 241, 0.07);
		color: #4f46e5;
	}

	.doctor-shell__nav-item.active {
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: #fff;
		box-shadow: 0 3px 10px rgba(99, 102, 241, 0.3);
	}

	/* Right: slot actions + logout */
	.doctor-shell__nav-right {
		display: flex;
		align-items: center;
		gap: 0.55rem;
		flex-shrink: 0;
		margin-left: auto;
		padding-left: 1.25rem;
		border-left: 1px solid #e5e7eb;
	}

	.doctor-shell__logout {
		border: 1px solid #e5e7eb;
		background: #fff;
		color: #374151;
		font-size: 0.82rem;
		font-weight: 600;
		padding: 0.44rem 1rem;
		border-radius: 7px;
		cursor: pointer;
		transition: background 130ms, border-color 130ms, color 130ms;
		white-space: nowrap;
	}

	.doctor-shell__logout:hover {
		background: #fef2f2;
		border-color: #fca5a5;
		color: #b91c1c;
	}

	/* ══════════════════════════════════════
	   PAGE BODY — centred column below nav
	══════════════════════════════════════ */
	.doctor-shell__body {
		flex: 1;
		max-width: var(--shell-max-width);
		width: 100%;
		margin: 0 auto;
		padding: 2.25rem 2rem 3.5rem;
		display: flex;
		flex-direction: column;
	}

	/* Page title strip — sits on the gradient, no box */
	.doctor-shell__page-header {
		margin-bottom: 1.5rem;
	}

	.doctor-shell__eyebrow {
		margin: 0 0 0.28rem;
		font-size: 0.69rem;
		font-weight: 800;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: #6366f1;
	}

	h1 {
		margin: 0;
		font-size: clamp(1.6rem, 2.8vw, 2.25rem);
		font-weight: 800;
		line-height: 1.1;
		color: #0f172a;
		letter-spacing: -0.02em;
	}

	.doctor-shell__subtitle {
		margin: 0.42rem 0 0;
		max-width: 660px;
		font-size: 0.9rem;
		line-height: 1.65;
		color: #475569;
	}

	/* ══════════════════════════════════════
	   CONTENT CARD — white box for all page content
	══════════════════════════════════════ */
	.doctor-shell__card {
		background: #fff;
		border-radius: 18px;
		border: 1px solid rgba(148, 163, 184, 0.16);
		box-shadow:
			0 0 0 1px rgba(255, 255, 255, 0.7) inset,
			0 8px 40px rgba(15, 23, 42, 0.07),
			0 2px 6px rgba(99, 102, 241, 0.04);
	}

	.doctor-shell__content {
		padding: 2rem;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	/* ══════════════════════════════════════
	   SETTINGS DROPDOWN
	══════════════════════════════════════ */
	.settings-wrapper {
		position: relative;
		display: flex;
		align-items: center;
	}

	.doctor-shell__settings-btn {
		display: flex;
		align-items: center;
		gap: 0.38rem;
		border: 1px solid #e5e7eb;
		background: #fff;
		color: #374151;
		font-size: 0.82rem;
		font-weight: 600;
		padding: 0.44rem 0.9rem;
		border-radius: 7px;
		cursor: pointer;
		transition: background 130ms, border-color 130ms, color 130ms, box-shadow 130ms;
		white-space: nowrap;
	}

	.doctor-shell__settings-btn:hover,
	.doctor-shell__settings-btn.active {
		background: #eef2ff;
		border-color: #c7d2fe;
		color: #4f46e5;
	}

	.settings-backdrop {
		position: fixed;
		inset: 0;
		z-index: 199;
	}

	.settings-panel {
		position: absolute;
		top: calc(100% + 10px);
		right: 0;
		z-index: 200;
		width: 310px;
		background: #ffffff;
		border: 1px solid rgba(99, 102, 241, 0.14);
		border-radius: 16px;
		box-shadow:
			0 4px 6px rgba(0, 0, 0, 0.04),
			0 12px 40px rgba(15, 23, 42, 0.13);
		overflow: hidden;
	}

	.settings-section {
		padding: 1.1rem 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
	}

	.settings-kicker {
		margin: 0;
		font-size: 0.69rem;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #4f46e5;
	}

	.settings-section-desc {
		margin: -0.3rem 0 0;
		font-size: 0.78rem;
		color: #64748b;
		line-height: 1.5;
	}

	.settings-field {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: #374151;
	}

	.settings-field input,
	.settings-field select {
		border: 1px solid #d1d5db;
		border-radius: 8px;
		padding: 0.52rem 0.75rem;
		font-size: 0.875rem;
		font-family: inherit;
		color: #111827;
		background: #f9fafb;
		transition: border-color 130ms, box-shadow 130ms;
		outline: none;
	}

	.settings-field input:focus,
	.settings-field select:focus {
		border-color: #6366f1;
		box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
		background: #fff;
	}

	.settings-save-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		margin-top: 0.15rem;
		width: 100%;
		padding: 0.6rem 1rem;
		border: none;
		border-radius: 8px;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: #fff;
		font-size: 0.84rem;
		font-weight: 700;
		cursor: pointer;
		transition: background 150ms, box-shadow 150ms;
		box-shadow: 0 3px 10px rgba(99, 102, 241, 0.25);
	}

	.settings-save-btn:hover {
		background: linear-gradient(135deg, #4338ca, #4f46e5);
		box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
	}

	.settings-save-btn.saved {
		background: linear-gradient(135deg, #059669, #10b981);
		box-shadow: 0 3px 10px rgba(16, 185, 129, 0.28);
	}

	.settings-divider {
		height: 1px;
		background: linear-gradient(to right, transparent, #e2e8f0, transparent);
		margin: 0 1.2rem;
	}

	/* ── Responsive ── */
	@media (max-width: 900px) {
		.doctor-shell__topbar-inner {
			height: auto;
			min-height: 56px;
			padding: 0.6rem 1rem;
			flex-wrap: wrap;
		}

		.doctor-shell__brand {
			border-right: none;
			padding-right: 0;
			margin-right: 0;
		}

		.doctor-shell__nav-items {
			order: 3;
			width: 100%;
			flex-wrap: wrap;
			padding-bottom: 0.25rem;
		}

		.doctor-shell__nav-right {
			margin-left: auto;
			border-left: none;
			padding-left: 0;
		}

		.doctor-shell__body {
			padding: 1.5rem 1rem 2.5rem;
		}

		.doctor-shell__content {
			padding: 1.25rem;
		}

		.doctor-shell__card {
			border-radius: 14px;
		}
	}
</style>
