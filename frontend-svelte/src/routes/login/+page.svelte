<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api.js';
	import { locale, translateText } from '$lib/i18n';
	import { clearUser, setUser } from '$lib/stores';
	import { get } from 'svelte/store';
	import { onMount } from 'svelte';

	let email = '';
	let password = '';
	let loginType = 'patient'; // 'patient' | 'doctor' | 'admin'
	let error = '';
	let loading = false;
	let showPassword = false;

	onMount(() => {
		if (get(page).url.searchParams.get('reset') === '1') {
			clearUser();
		}
	});

	async function handleLogin() {
		error = '';
		if (!email || !password) { error = 'Please fill in all fields'; return; }
		loading = true;
		try {
			const endpoint = loginType === 'doctor'
				? '/api/auth/doctor/login'
				: loginType === 'admin'
				? '/api/admin/login'
				: '/api/auth/login';

			const response = await api.post(endpoint, { email, password });
			setUser({
				id:       response.data.id,
				email:    response.data.email,
				role:     response.data.role || loginType,
				fullName: response.data.full_name || null
			});

			if      (loginType === 'doctor') goto('/doctor/dashboard');
			else if (loginType === 'admin')  goto('/admin/dashboard');
			else                             goto('/dashboard');
		} catch (err) {
			error = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
		} finally {
			loading = false;
		}
	}

	function getLoginButtonLabel(type, activeLocale) {
		if (type === 'doctor') return translateText('Sign in as Clinician', activeLocale);
		if (type === 'admin')  return translateText('Sign in as Admin', activeLocale);
		return translateText('Sign in', activeLocale);
	}

	$: loginButtonLabel = loading
		? translateText('Signing in…', $locale)
		: getLoginButtonLabel(loginType, $locale);
</script>

<svelte:head>
	<title>Sign In — NeuroBloom</title>
</svelte:head>

<div class="login-shell">

	<!-- LEFT — brand panel -->
	<div class="brand-panel" aria-hidden="true">
		<div class="brand-glow brand-glow-1"></div>
		<div class="brand-glow brand-glow-2"></div>

		<div class="brand-inner">
			<!-- Logo mark -->
			<div class="logo-mark">
				<svg width="44" height="44" viewBox="0 0 44 44" fill="none">
					<circle cx="22" cy="22" r="22" fill="rgba(14,165,233,0.12)"/>
					<circle cx="22" cy="22" r="14" fill="rgba(14,165,233,0.18)"/>
					<circle cx="22" cy="22" r="7"  fill="#38bdf8"/>
				</svg>
			</div>

			<h1 class="brand-name">NeuroBloom</h1>
			<p class="brand-tagline">Cognitive Rehabilitation Platform</p>

			<div class="feature-list">
				<div class="feature-item">
					<div class="feature-icon">
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
							<path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div>
						<div class="feature-title">Personalised Assessments</div>
						<div class="feature-desc">Validated baseline tasks across 6 cognitive domains</div>
					</div>
				</div>
				<div class="feature-item">
					<div class="feature-icon">
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z"/>
							<path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z"/>
						</svg>
					</div>
					<div>
						<div class="feature-title">Progress Analytics</div>
						<div class="feature-desc">Track cognitive trends over time with clinical insights</div>
					</div>
				</div>
				<div class="feature-item">
					<div class="feature-icon">
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div>
						<div class="feature-title">Adaptive Training</div>
						<div class="feature-desc">AI-driven exercises that adjust to your performance</div>
					</div>
				</div>
			</div>
		</div>

		<div class="brand-footer">
			Designed for MS cognitive care
		</div>
	</div>

	<!-- RIGHT — form panel -->
	<div class="form-panel">
		<div class="form-inner">

			<!-- Mobile logo (hidden on desktop) -->
			<div class="mobile-logo">
				<div class="mobile-logo-dot"></div>
				<span>NeuroBloom</span>
			</div>

			<div class="form-header">
				<h2>Welcome back</h2>
				<p>Sign in to continue your cognitive journey</p>
			</div>

			<!-- Role selector -->
			<div class="role-selector">
				<button
					type="button"
					class="role-btn {loginType === 'patient' ? 'role-active' : ''}"
					on:click={() => loginType = 'patient'}
					disabled={loading}
				>
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
						<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
					</svg>
					{translateText('Patient', $locale)}
				</button>
				<button
					type="button"
					class="role-btn {loginType === 'doctor' ? 'role-active' : ''}"
					on:click={() => loginType = 'doctor'}
					disabled={loading}
				>
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
						<path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
					</svg>
					{translateText('Clinician', $locale)}
				</button>
				<button
					type="button"
					class="role-btn {loginType === 'admin' ? 'role-active' : ''}"
					on:click={() => loginType = 'admin'}
					disabled={loading}
				>
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
						<path fill-rule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
					</svg>
					{translateText('Admin', $locale)}
				</button>
			</div>

			{#if error}
				<div class="error-banner">
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16" style="flex-shrink:0">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
					</svg>
					{error}
				</div>
			{/if}

			<form on:submit|preventDefault={handleLogin} novalidate>
				<div class="field">
					<label for="email">Email address</label>
					<div class="input-wrap">
						<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
							<path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
						</svg>
						<input
							type="email"
							id="email"
							bind:value={email}
							placeholder="you@example.com"
							disabled={loading}
							autocomplete="email"
						/>
					</div>
				</div>

				<div class="field">
					<label for="password">Password</label>
					<div class="input-wrap">
						<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
						</svg>
						<input
							type={showPassword ? 'text' : 'password'}
							id="password"
							bind:value={password}
							placeholder="••••••••"
							disabled={loading}
							autocomplete="current-password"
						/>
						<button
							type="button"
							class="toggle-pw"
							on:click={() => showPassword = !showPassword}
							tabindex="-1"
							aria-label={showPassword ? 'Hide password' : 'Show password'}
						>
							{#if showPassword}
								<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
									<path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/>
									<path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
								</svg>
							{:else}
								<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
									<path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
									<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
								</svg>
							{/if}
						</button>
					</div>
				</div>

				<button type="submit" class="submit-btn" disabled={loading}>
					{#if loading}
						<span class="spinner"></span>
					{/if}
					{loginButtonLabel}
				</button>
			</form>

			<p class="register-link">
				{translateText("Don't have an account?", $locale)}
				<a href="/register">{translateText('Create one', $locale)}</a>
			</p>

		</div>
	</div>
</div>

<style>
	:global(body) { background: #060d1a !important; }

	/* ── Shell ─────────────────────────────────────────── */
	.login-shell {
		display: flex;
		min-height: 100vh;
		background: #060d1a;
	}

	/* ── Brand panel ───────────────────────────────────── */
	.brand-panel {
		flex: 0 0 46%;
		background: #060d1a;
		border-right: 1px solid rgba(255,255,255,0.06);
		position: relative;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding: 3rem 3.5rem;
	}

	.brand-glow {
		position: absolute;
		border-radius: 50%;
		filter: blur(100px);
		pointer-events: none;
	}
	.brand-glow-1 {
		width: 380px; height: 380px;
		background: rgba(14, 165, 233, 0.13);
		top: -100px; right: -80px;
	}
	.brand-glow-2 {
		width: 280px; height: 280px;
		background: rgba(56, 189, 248, 0.07);
		bottom: 40px; left: -60px;
	}

	.brand-inner { position: relative; z-index: 1; }

	.logo-mark { margin-bottom: 1.25rem; }

	.brand-name {
		font-size: 2.25rem;
		font-weight: 800;
		color: #f0f9ff;
		letter-spacing: -0.5px;
		margin: 0 0 0.4rem;
	}

	.brand-tagline {
		font-size: 0.95rem;
		color: rgba(186,230,253,0.55);
		font-weight: 400;
		margin: 0 0 3rem;
		letter-spacing: 0.3px;
	}

	.feature-list {
		display: flex;
		flex-direction: column;
		gap: 1.35rem;
	}

	.feature-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
	}

	.feature-icon {
		width: 36px; height: 36px;
		background: rgba(14,165,233,0.12);
		border: 1px solid rgba(14,165,233,0.2);
		border-radius: 10px;
		display: flex; align-items: center; justify-content: center;
		color: #38bdf8;
		flex-shrink: 0;
		margin-top: 2px;
	}

	.feature-title {
		font-size: 0.92rem;
		font-weight: 700;
		color: #e0f2fe;
		margin-bottom: 0.2rem;
	}

	.feature-desc {
		font-size: 0.82rem;
		color: rgba(148,185,212,0.6);
		line-height: 1.4;
	}

	.brand-footer {
		position: relative; z-index: 1;
		font-size: 0.78rem;
		color: rgba(148,185,212,0.35);
		letter-spacing: 0.3px;
	}

	/* ── Form panel ────────────────────────────────────── */
	.form-panel {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #ffffff;
		padding: 2.5rem 2rem;
	}

	.form-inner {
		width: 100%;
		max-width: 420px;
	}

	/* Mobile logo (shown only on small screens) */
	.mobile-logo {
		display: none;
		align-items: center;
		gap: 0.6rem;
		margin-bottom: 2rem;
	}
	.mobile-logo-dot {
		width: 28px; height: 28px;
		background: #0c1a2e;
		border-radius: 8px;
	}
	.mobile-logo span {
		font-size: 1.25rem;
		font-weight: 800;
		color: #0f172a;
		letter-spacing: -0.3px;
	}

	/* Form header */
	.form-header { margin-bottom: 2rem; }
	.form-header h2 {
		font-size: 1.8rem;
		font-weight: 800;
		color: #0c1a2e;
		letter-spacing: -0.5px;
		margin: 0 0 0.35rem;
	}
	.form-header p {
		font-size: 0.9rem;
		color: #64748b;
		margin: 0;
	}

	/* Role selector */
	.role-selector {
		display: flex;
		background: #f1f5f9;
		border-radius: 10px;
		padding: 4px;
		gap: 4px;
		margin-bottom: 1.5rem;
	}

	.role-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		padding: 0.6rem 0.5rem;
		border: none;
		background: transparent;
		border-radius: 7px;
		cursor: pointer;
		font-size: 0.82rem;
		font-weight: 600;
		color: #64748b;
		transition: background 0.18s, color 0.18s, box-shadow 0.18s;
		white-space: nowrap;
	}
	.role-btn:hover:not(:disabled):not(.role-active) {
		background: rgba(255,255,255,0.6);
		color: #475569;
	}
	.role-btn.role-active {
		background: white;
		color: #0369a1;
		box-shadow: 0 1px 6px rgba(0,0,0,0.1);
	}
	.role-btn:disabled { opacity: 0.55; cursor: not-allowed; }

	/* Error banner */
	.error-banner {
		display: flex;
		align-items: flex-start;
		gap: 0.6rem;
		background: #fff1f2;
		border: 1px solid #fecdd3;
		color: #be123c;
		padding: 0.8rem 1rem;
		border-radius: 10px;
		font-size: 0.875rem;
		font-weight: 500;
		margin-bottom: 1.25rem;
		line-height: 1.4;
	}

	/* Fields */
	.field { margin-bottom: 1.25rem; }

	.field label {
		display: block;
		font-size: 0.83rem;
		font-weight: 600;
		color: #374151;
		margin-bottom: 0.45rem;
		letter-spacing: 0.2px;
	}

	.input-wrap {
		position: relative;
		display: flex;
		align-items: center;
	}

	.input-icon {
		position: absolute;
		left: 0.9rem;
		color: #94a3b8;
		pointer-events: none;
		flex-shrink: 0;
	}

	.input-wrap input {
		width: 100%;
		padding: 0.75rem 0.9rem 0.75rem 2.6rem;
		border: 1.5px solid #e2e8f0;
		border-radius: 10px;
		font-size: 0.95rem;
		color: #0f172a;
		background: #f8fafc;
		transition: border-color 0.18s, background 0.18s, box-shadow 0.18s;
		outline: none;
	}
	.input-wrap input::placeholder { color: #cbd5e1; }
	.input-wrap input:focus {
		border-color: #0ea5e9;
		background: white;
		box-shadow: 0 0 0 3px rgba(14,165,233,0.1);
	}
	.input-wrap input:disabled { opacity: 0.6; cursor: not-allowed; }

	.toggle-pw {
		position: absolute;
		right: 0.75rem;
		background: none;
		border: none;
		color: #94a3b8;
		cursor: pointer;
		padding: 0.25rem;
		display: flex; align-items: center;
		border-radius: 4px;
		transition: color 0.15s;
	}
	.toggle-pw:hover { color: #64748b; }

	/* Submit */
	.submit-btn {
		width: 100%;
		padding: 0.85rem;
		margin-top: 0.5rem;
		background: #0c1a2e;
		color: white;
		border: none;
		border-radius: 10px;
		font-size: 0.95rem;
		font-weight: 700;
		cursor: pointer;
		display: flex; align-items: center; justify-content: center; gap: 0.5rem;
		transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s, background 0.2s;
		letter-spacing: 0.2px;
	}
	.submit-btn:hover:not(:disabled) {
		transform: translateY(-1px);
		background: #0f2744;
		box-shadow: 0 8px 24px rgba(12,26,46,0.35);
	}
	.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

	/* Spinner */
	.spinner {
		width: 16px; height: 16px;
		border: 2px solid rgba(255,255,255,0.35);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		flex-shrink: 0;
	}
	@keyframes spin { to { transform: rotate(360deg); } }

	/* Register link */
	.register-link {
		text-align: center;
		margin-top: 1.5rem;
		font-size: 0.875rem;
		color: #64748b;
	}
	.register-link a {
		color: #0369a1;
		font-weight: 700;
		text-decoration: none;
		margin-left: 0.3rem;
	}
	.register-link a:hover { text-decoration: underline; }

	/* ── Responsive ────────────────────────────────────── */
	@media (max-width: 768px) {
		.login-shell    { flex-direction: column; }
		.brand-panel    { display: none; }
		.form-panel     { padding: 2rem 1.5rem; align-items: flex-start; padding-top: 3rem; }
		.mobile-logo    { display: flex; }
	}
</style>
