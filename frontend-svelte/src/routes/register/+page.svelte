<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';

	let email = '';
	let password = '';
	let confirmPassword = '';
	let registerType = 'patient'; // 'patient' | 'doctor'
	let fullName = '';
	let licenseNumber = '';
	let specialization = '';
	let institution = '';
	let error = '';
	let success = '';
	let loading = false;
	let showPassword = false;
	let showConfirm = false;

	async function handleRegister() {
		error = '';
		success = '';

		if (!email || !password || !confirmPassword || !fullName) {
			error = 'Please fill in all required fields';
			return;
		}
		if (registerType === 'doctor' && (!licenseNumber || !specialization)) {
			error = 'Please fill in all required clinician fields';
			return;
		}
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}
		if (password.length < 6) {
			error = 'Password must be at least 6 characters';
			return;
		}

		loading = true;
		try {
			if (registerType === 'doctor') {
				await api.post('/api/auth/doctor/register', {
					email, password,
					full_name: fullName,
					license_number: licenseNumber,
					specialization,
					institution: institution || null
				});
				success = 'Clinician account created. Your account is pending admin verification — you will be notified when approved.';
				setTimeout(() => goto('/login'), 4000);
			} else {
				await api.post('/api/auth/register', { email, password, full_name: fullName });
				goto('/login');
			}
		} catch (err) {
			error = err.response?.data?.detail || 'Registration failed. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Create Account — NeuroBloom</title>
</svelte:head>

<div class="reg-shell">

	<!-- LEFT — brand panel (identical to login) -->
	<div class="brand-panel" aria-hidden="true">
		<div class="brand-glow brand-glow-1"></div>
		<div class="brand-glow brand-glow-2"></div>

		<div class="brand-inner">
			<div class="logo-mark">
				<svg width="44" height="44" viewBox="0 0 44 44" fill="none">
					<circle cx="22" cy="22" r="22" fill="rgba(14,165,233,0.12)"/>
					<circle cx="22" cy="22" r="14" fill="rgba(14,165,233,0.18)"/>
					<circle cx="22" cy="22" r="7"  fill="#38bdf8"/>
				</svg>
			</div>

			<h1 class="brand-name">NeuroBloom</h1>
				<p class="brand-tagline">Start your cognitive care journey today</p>

			<div class="feature-list">
				<div class="feature-item">
					<div class="feature-icon">
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path fill-rule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
						</svg>
					</div>
					<div>
						<div class="feature-title">Secure &amp; Private</div>
						<div class="feature-desc">Your health data is encrypted and never shared without consent</div>
					</div>
				</div>
				<div class="feature-item">
					<div class="feature-icon">
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/>
						</svg>
					</div>
					<div>
						<div class="feature-title">Evidence-Based Tasks</div>
						<div class="feature-desc">Clinically validated assessments used in MS rehabilitation research</div>
					</div>
				</div>
				<div class="feature-item">
					<div class="feature-icon">
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
						</svg>
					</div>
					<div>
						<div class="feature-title">Clinician-Supervised</div>
						<div class="feature-desc">Your assigned clinician monitors progress and adjusts your training plan</div>
					</div>
				</div>
			</div>
		</div>

		<div class="brand-footer">Trusted by MS care teams worldwide</div>
	</div>

	<!-- RIGHT — form panel -->
	<div class="form-panel">
		<div class="form-inner">

			<!-- Mobile logo -->
			<div class="mobile-logo">
				<div class="mobile-logo-dot"></div>
				<span>NeuroBloom</span>
			</div>

			<div class="form-header">
				<h2>Create your account</h2>
				<p>Join NeuroBloom and start your cognitive journey</p>
			</div>

			<!-- Role selector -->
			<div class="role-selector">
				<button
					type="button"
					class="role-btn {registerType === 'patient' ? 'role-active' : ''}"
					on:click={() => registerType = 'patient'}
					disabled={loading}
				>
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
						<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
					</svg>
					Patient
				</button>
				<button
					type="button"
					class="role-btn {registerType === 'doctor' ? 'role-active' : ''}"
					on:click={() => registerType = 'doctor'}
					disabled={loading}
				>
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
						<path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
					</svg>
					Clinician
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

			{#if success}
				<div class="success-banner">
					<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16" style="flex-shrink:0">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
					</svg>
					{success}
				</div>
			{/if}

			<form on:submit|preventDefault={handleRegister} novalidate>

				<!-- Full name -->
				<div class="field">
					<label for="fullName">Full name</label>
					<div class="input-wrap">
						<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
							<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
						</svg>
						<input
							type="text"
							id="fullName"
							bind:value={fullName}
							placeholder={registerType === 'doctor' ? 'Dr. Jane Smith' : 'Jane Smith'}
							disabled={loading}
							autocomplete="name"
						/>
					</div>
				</div>

				<!-- Email -->
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

				<!-- Clinician-only fields -->
				{#if registerType === 'doctor'}
					<div class="clinician-section">
						<div class="section-label">
							<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
								<path fill-rule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
							</svg>
							Clinician credentials
						</div>

						<div class="field">
							<label for="licenseNumber">Medical licence number <span class="req">*</span></label>
							<div class="input-wrap">
								<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
									<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
								</svg>
								<input
									type="text"
									id="licenseNumber"
									bind:value={licenseNumber}
									placeholder="e.g. GMC-123456"
									disabled={loading}
								/>
							</div>
						</div>

						<div class="field">
							<label for="specialization">Specialisation <span class="req">*</span></label>
							<div class="input-wrap">
								<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
									<path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zm5.99 7.176A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z"/>
								</svg>
								<input
									type="text"
									id="specialization"
									bind:value={specialization}
									placeholder="e.g. Neurology, Psychiatry"
									disabled={loading}
								/>
							</div>
						</div>

						<div class="field">
							<label for="institution">
								Institution
								<span class="optional">optional</span>
							</label>
							<div class="input-wrap">
								<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
									<path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4zm7 5a1 1 0 10-2 0v1H8a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V9z" clip-rule="evenodd"/>
								</svg>
								<input
									type="text"
									id="institution"
									bind:value={institution}
									placeholder="Hospital or clinic name"
									disabled={loading}
								/>
							</div>
						</div>

						<div class="verification-notice">
							<svg viewBox="0 0 20 20" fill="currentColor" width="15" height="15" style="flex-shrink:0;margin-top:1px">
								<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
							</svg>
							Clinician accounts require admin verification before login access is granted.
						</div>
					</div>
				{/if}

				<!-- Password row -->
				<div class="field-row">
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
								placeholder="Min. 6 characters"
								disabled={loading}
								autocomplete="new-password"
							/>
							<button type="button" class="toggle-pw" on:click={() => showPassword = !showPassword} tabindex="-1" aria-label="Toggle password visibility">
								{#if showPassword}
									<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/><path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/></svg>
								{:else}
									<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
								{/if}
							</button>
						</div>
					</div>

					<div class="field">
						<label for="confirmPassword">Confirm password</label>
						<div class="input-wrap">
							<svg class="input-icon" viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
								<path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
							</svg>
							<input
								type={showConfirm ? 'text' : 'password'}
								id="confirmPassword"
								bind:value={confirmPassword}
								placeholder="Repeat password"
								disabled={loading}
								autocomplete="new-password"
								class:input-mismatch={confirmPassword && password !== confirmPassword}
							/>
							<button type="button" class="toggle-pw" on:click={() => showConfirm = !showConfirm} tabindex="-1" aria-label="Toggle confirm password visibility">
								{#if showConfirm}
									<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/><path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/></svg>
								{:else}
									<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
								{/if}
							</button>
						</div>
					</div>
				</div>

				<button type="submit" class="submit-btn" disabled={loading || !!success}>
					{#if loading}
						<span class="spinner"></span>
						Creating account…
					{:else if success}
						<svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
						Account created
					{:else}
						Create {registerType === 'doctor' ? 'clinician' : 'patient'} account
					{/if}
				</button>
			</form>

			<p class="login-link">
				Already have an account?
				<a href="/login">Sign in</a>
			</p>
		</div>
	</div>
</div>

<style>
	:global(body) { background: #060d1a !important; }

	/* ── Shell ──────────────────────────────────────────── */
	.reg-shell {
		display: flex;
		min-height: 100vh;
		background: #060d1a;
	}

	/* ── Brand panel ─────────────────────────────────────── */
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
	.brand-glow { position: absolute; border-radius: 50%; filter: blur(100px); pointer-events: none; }
	.brand-glow-1 { width: 380px; height: 380px; background: rgba(14,165,233,0.13); top: -100px; right: -80px; }
	.brand-glow-2 { width: 280px; height: 280px; background: rgba(56,189,248,0.07); bottom: 40px; left: -60px; }

	.brand-inner { position: relative; z-index: 1; }
	.logo-mark   { margin-bottom: 1.25rem; }

	.brand-name {
		font-size: 2.25rem; font-weight: 800; color: #f0f9ff;
		letter-spacing: -0.5px; margin: 0 0 0.4rem;
	}
	.brand-tagline {
		font-size: 0.95rem; color: rgba(186,230,253,0.55);
		font-weight: 400; margin: 0 0 3rem; letter-spacing: 0.3px;
	}
	.feature-list { display: flex; flex-direction: column; gap: 1.35rem; }
	.feature-item { display: flex; align-items: flex-start; gap: 1rem; }
	.feature-icon {
		width: 36px; height: 36px;
		background: rgba(14,165,233,0.12); border: 1px solid rgba(14,165,233,0.2);
		border-radius: 10px; display: flex; align-items: center; justify-content: center;
		color: #38bdf8; flex-shrink: 0; margin-top: 2px;
	}
	.feature-title { font-size: 0.92rem; font-weight: 700; color: #e0f2fe; margin-bottom: 0.2rem; }
	.feature-desc  { font-size: 0.82rem; color: rgba(148,185,212,0.6); line-height: 1.4; }
	.brand-footer  { position: relative; z-index: 1; font-size: 0.78rem; color: rgba(148,185,212,0.35); letter-spacing: 0.3px; }

	/* ── Form panel ──────────────────────────────────────── */
	.form-panel {
		flex: 1;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		background: #ffffff;
		padding: 3rem 2rem;
		padding-top: 5rem;
		overflow-y: auto;
	}
	.form-inner { width: 100%; max-width: 480px; }

	/* Mobile logo */
	.mobile-logo { display: none; align-items: center; gap: 0.6rem; margin-bottom: 2rem; }
	.mobile-logo-dot { width: 28px; height: 28px; background: #0c1a2e; border-radius: 8px; }
	.mobile-logo span { font-size: 1.25rem; font-weight: 800; color: #0c1a2e; letter-spacing: -0.3px; }

	/* Form header */
	.form-header { margin-bottom: 1.75rem; }
	.form-header h2 { font-size: 1.8rem; font-weight: 800; color: #0c1a2e; letter-spacing: -0.5px; margin: 0 0 0.35rem; }
	.form-header p  { font-size: 0.9rem; color: #64748b; margin: 0; }

	/* Role selector */
	.role-selector {
		display: flex; background: #f1f5f9; border-radius: 10px;
		padding: 4px; gap: 4px; margin-bottom: 1.5rem;
	}
	.role-btn {
		flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.4rem;
		padding: 0.6rem 0.5rem; border: none; background: transparent; border-radius: 7px;
		cursor: pointer; font-size: 0.82rem; font-weight: 600; color: #64748b;
		transition: background 0.18s, color 0.18s, box-shadow 0.18s; white-space: nowrap;
	}
	.role-btn:hover:not(:disabled):not(.role-active) { background: rgba(255,255,255,0.6); color: #475569; }
	.role-btn.role-active { background: white; color: #0369a1; box-shadow: 0 1px 6px rgba(0,0,0,0.1); }
	.role-btn:disabled { opacity: 0.55; cursor: not-allowed; }

	/* Banners */
	.error-banner {
		display: flex; align-items: flex-start; gap: 0.6rem;
		background: #fff1f2; border: 1px solid #fecdd3; color: #be123c;
		padding: 0.8rem 1rem; border-radius: 10px;
		font-size: 0.875rem; font-weight: 500; margin-bottom: 1.25rem; line-height: 1.4;
	}
	.success-banner {
		display: flex; align-items: flex-start; gap: 0.6rem;
		background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d;
		padding: 0.8rem 1rem; border-radius: 10px;
		font-size: 0.875rem; font-weight: 500; margin-bottom: 1.25rem; line-height: 1.5;
	}

	/* Fields */
	.field { margin-bottom: 1.1rem; }
	.field label {
		display: block; font-size: 0.83rem; font-weight: 600;
		color: #374151; margin-bottom: 0.45rem; letter-spacing: 0.2px;
	}
	.req      { color: #e11d48; margin-left: 2px; }
	.optional { font-size: 0.75rem; font-weight: 500; color: #94a3b8; margin-left: 0.35rem; }

	/* Side-by-side password row */
	.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }

	/* Input */
	.input-wrap { position: relative; display: flex; align-items: center; }
	.input-icon { position: absolute; left: 0.9rem; color: #94a3b8; pointer-events: none; flex-shrink: 0; }
	.input-wrap input {
		width: 100%; padding: 0.75rem 0.9rem 0.75rem 2.6rem;
		border: 1.5px solid #e2e8f0; border-radius: 10px; font-size: 0.9rem;
		color: #0f172a; background: #f8fafc;
		transition: border-color 0.18s, background 0.18s, box-shadow 0.18s; outline: none;
	}
	.input-wrap input::placeholder { color: #cbd5e1; }
	.input-wrap input:focus { border-color: #0ea5e9; background: white; box-shadow: 0 0 0 3px rgba(14,165,233,0.1); }
	.input-wrap input:disabled { opacity: 0.6; cursor: not-allowed; }
	.input-mismatch { border-color: #fca5a5 !important; background: #fff1f2 !important; }

	.toggle-pw {
		position: absolute; right: 0.75rem; background: none; border: none;
		color: #94a3b8; cursor: pointer; padding: 0.25rem;
		display: flex; align-items: center; border-radius: 4px; transition: color 0.15s;
	}
	.toggle-pw:hover { color: #64748b; }

	/* Clinician section */
	.clinician-section {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.25rem 1.25rem 0.25rem;
		margin-bottom: 1.1rem;
	}
	.section-label {
		display: flex; align-items: center; gap: 0.4rem;
		font-size: 0.78rem; font-weight: 700; text-transform: uppercase;
		letter-spacing: 0.5px; color: #0369a1; margin-bottom: 1rem;
	}
	.verification-notice {
		display: flex; align-items: flex-start; gap: 0.5rem;
		font-size: 0.8rem; color: #64748b; line-height: 1.45;
		background: #f0f9ff; border: 1px solid #bae6fd;
		border-radius: 8px; padding: 0.65rem 0.85rem;
		margin: 0.5rem 0 1rem;
	}

	/* Submit */
	.submit-btn {
		width: 100%; padding: 0.85rem; margin-top: 0.25rem;
		background: #0c1a2e; color: white; border: none; border-radius: 10px;
		font-size: 0.95rem; font-weight: 700; cursor: pointer;
		display: flex; align-items: center; justify-content: center; gap: 0.5rem;
		transition: background 0.2s, transform 0.2s, box-shadow 0.2s; letter-spacing: 0.2px;
	}
	.submit-btn:hover:not(:disabled) { transform: translateY(-1px); background: #0f2744; box-shadow: 0 8px 24px rgba(12,26,46,0.35); }
	.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

	.spinner {
		width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.35);
		border-top-color: white; border-radius: 50%;
		animation: spin 0.7s linear infinite; flex-shrink: 0;
	}
	@keyframes spin { to { transform: rotate(360deg); } }

	/* Login link */
	.login-link { text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: #64748b; }
	.login-link a { color: #0369a1; font-weight: 700; text-decoration: none; margin-left: 0.3rem; }
	.login-link a:hover { text-decoration: underline; }

	/* ── Responsive ──────────────────────────────────────── */
	@media (max-width: 768px) {
		.reg-shell    { flex-direction: column; }
		.brand-panel  { display: none; }
		.form-panel   { padding: 2rem 1.5rem; align-items: flex-start; padding-top: 3rem; }
		.mobile-logo  { display: flex; }
		.field-row    { grid-template-columns: 1fr; }
	}
</style>
