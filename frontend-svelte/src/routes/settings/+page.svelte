<script>
	import { goto } from '$app/navigation';
	import PatientShell from '$lib/components/patient-dashboard/PatientShell.svelte';
	import LanguagePreferencePanel from '$lib/components/LanguagePreferencePanel.svelte';
	import api from '$lib/api.js';
	import { locale, localeText } from '$lib/i18n';
	import { clearUser, user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let saving = false;
	let error = '';
	let message = '';
	let consentToShare = false;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	$: header = {
		brand: 'NeuroBloom',
		title: lt('Settings', 'সেটিংস'),
		subtitle: currentUser?.full_name || currentUser?.email || lt('Patient', 'রোগী'),
		description: lt(
			'Manage language, privacy, and a few app-level preferences without mixing them into your profile.',
			'প্রোফাইলের সঙ্গে না মিশিয়ে এখানে ভাষা, গোপনীয়তা ও অ্যাপ-সংক্রান্ত পছন্দগুলো নিয়ন্ত্রণ করুন।'
		),
		logoutLabel: lt('Logout', 'লগআউট')
	};

	$: headerActions = [
		{ label: lt('Notifications', 'নোটিফিকেশন'), href: '/notifications' },
		{ label: lt('Messages', 'বার্তা'), href: '/messages' },
		{ label: lt('Profile', 'প্রোফাইল'), href: '/profile' },
		{ type: 'logout', label: lt('Logout', 'লগআউট') }
	];

	onMount(async () => {
		if (!currentUser || currentUser.role !== 'patient') {
			goto('/login');
			return;
		}

		try {
			const response = await api.get(`/api/auth/patient/${currentUser.id}/profile`);
			consentToShare = Boolean(response.data?.consent_to_share);
		} catch (loadError) {
			console.error('Failed to load settings:', loadError);
			error = lt('We could not load your settings.', 'আপনার সেটিংস লোড করা যায়নি।');
		} finally {
			loading = false;
		}
	});

	async function toggleConsent() {
		saving = true;
		error = '';
		message = '';

		try {
			const response = await api.patch(
				`/api/auth/patient/${currentUser.id}/consent`,
				null,
				{ params: { consent: !consentToShare } }
			);

			consentToShare = Boolean(response.data?.consent_to_share);
			message = lt('Privacy settings updated.', 'গোপনীয়তার সেটিংস হালনাগাদ হয়েছে।');
		} catch (updateError) {
			console.error('Failed to update consent:', updateError);
			error =
				updateError.response?.data?.detail ||
				lt('We could not update your privacy settings.', 'আপনার গোপনীয়তার সেটিংস হালনাগাদ করা যায়নি।');
		} finally {
			saving = false;
		}
	}

	function handleLogout() {
		clearUser();
		goto('/login');
	}
</script>

<PatientShell {header} actions={headerActions} warnings={error ? [error] : []} on:logout={handleLogout}>
	<div slot="main-top" class="page-stack">
		<section class="panel-card">
			<p class="eyebrow">{lt('Language', 'ভাষা')}</p>
			<h2>{lt('Choose the language that feels most comfortable.', 'যে ভাষায় সবচেয়ে স্বাচ্ছন্দ্যবোধ করেন তা বেছে নিন।')}</h2>
			<p class="description">{lt('This changes your patient-facing workspace, navigation, and supporting copy.', 'এটি আপনার রোগী-ওয়ার্কস্পেস, নেভিগেশন ও সহায়ক লেখাগুলো পরিবর্তন করবে।')}</p>

			<div class="content-block">
				<LanguagePreferencePanel />
			</div>
		</section>
	</div>

	<div slot="rail" class="page-stack">
		<section class="panel-card">
			<p class="eyebrow">{lt('Account routes', 'অ্যাকাউন্ট রুট')}</p>
			<div class="link-grid">
				<a href="/profile">{lt('Open profile', 'প্রোফাইল খুলুন')}</a>
				<a href="/dashboard">{lt('Back to dashboard', 'ড্যাশবোর্ডে ফিরুন')}</a>
				<a href="/notifications">{lt('Notifications', 'নোটিফিকেশন')}</a>
			</div>
		</section>
	</div>

	<div slot="main-bottom" class="page-stack">
		<section class="panel-card">
			<div class="section-head">
				<div>
					<p class="eyebrow">{lt('Privacy', 'গোপনীয়তা')}</p>
					<h3>{lt('Control care-team visibility', 'কেয়ার টিমের দৃশ্যমানতা নিয়ন্ত্রণ করুন')}</h3>
				</div>
				<button class="toggle-btn" on:click={toggleConsent} disabled={saving || loading}>
					{#if saving}
						{lt('Updating...', 'হালনাগাদ হচ্ছে...')}
					{:else if consentToShare}
						{lt('Disable sharing', 'শেয়ারিং বন্ধ করুন')}
					{:else}
						{lt('Enable sharing', 'শেয়ারিং চালু করুন')}
					{/if}
				</button>
			</div>

			<div class="privacy-state {consentToShare ? 'enabled' : 'disabled'}">
				<div>
					<p class="state-label">{lt('Current status', 'বর্তমান অবস্থা')}</p>
					<strong>{consentToShare ? lt('Healthcare providers can review your progress.', 'স্বাস্থ্যসেবা প্রদানকারীরা আপনার অগ্রগতি দেখতে পারবেন।') : lt('Your training data stays private to you.', 'আপনার ট্রেনিং ডেটা আপাতত শুধু আপনার কাছেই থাকবে।')}</strong>
				</div>
				<p class="muted">
					{consentToShare
						? lt('Doctors can use your progress, baseline results, and care notes to support you more personally.', 'ডাক্তাররা আপনার অগ্রগতি, বেসলাইন ফলাফল ও কেয়ার নোট ব্যবহার করে আরও ব্যক্তিগত সহায়তা দিতে পারবেন।')
						: lt('Without consent, doctors cannot review your patient data or provide guided monitoring.', 'কনসেন্ট ছাড়া ডাক্তাররা আপনার রোগী-সংক্রান্ত ডেটা দেখতে বা নির্দেশিত পর্যবেক্ষণ দিতে পারবেন না।')}
				</p>
			</div>

			{#if message}
				<p class="success">{message}</p>
			{/if}
		</section>
	</div>
</PatientShell>

<style>
	.page-stack {
		display: grid;
		gap: 1rem;
	}

	.panel-card {
		padding: 1.25rem;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(203, 213, 225, 0.76);
		box-shadow: 0 16px 32px rgba(15, 23, 42, 0.05);
	}

	.eyebrow,
	h2,
	h3,
	.description,
	.muted,
	.success,
	.state-label {
		margin: 0;
	}

	.eyebrow {
		font-size: 0.76rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #0369a1;
	}

	h2 {
		margin-top: 0.3rem;
		font-size: clamp(1.5rem, 3vw, 2rem);
		line-height: 1.18;
		color: #0f172a;
		max-width: 28ch;
	}

	h3 {
		margin-top: 0.25rem;
		font-size: 1.22rem;
		color: #0f172a;
	}

	.description,
	.muted,
	.success {
		line-height: 1.6;
		color: #64748b;
	}

	.description {
		margin-top: 0.65rem;
		max-width: 60ch;
	}

	.content-block {
		margin-top: 1rem;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.toggle-btn {
		border: none;
		border-radius: 999px;
		padding: 0.85rem 1.1rem;
		background: linear-gradient(135deg, #0f766e, #0ea5a4);
		color: #fff;
		font-weight: 800;
		cursor: pointer;
	}

	.toggle-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.privacy-state {
		padding: 1rem;
		border-radius: 18px;
		border: 1px solid rgba(203, 213, 225, 0.76);
		display: grid;
		gap: 0.55rem;
	}

	.privacy-state.enabled {
		background: rgba(236, 253, 245, 0.92);
		border-color: rgba(52, 211, 153, 0.38);
	}

	.privacy-state.disabled {
		background: rgba(248, 250, 252, 0.9);
	}

	.state-label {
		font-size: 0.8rem;
		font-weight: 700;
		color: #64748b;
	}

	.privacy-state strong {
		color: #0f172a;
	}

	.link-grid {
		display: grid;
		gap: 0.75rem;
		margin-top: 0.8rem;
	}

	.link-grid a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.82rem 1rem;
		border-radius: 999px;
		text-decoration: none;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.8);
		color: #0f172a;
		font-weight: 800;
	}

	.success {
		margin-top: 0.9rem;
		color: #047857;
		font-weight: 700;
	}

	@media (max-width: 900px) {
		.section-head {
			flex-direction: column;
		}
	}
</style>
