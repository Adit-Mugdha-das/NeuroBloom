<script>
	import { goto } from '$app/navigation';
	import DashboardActionStrip from '$lib/components/patient-dashboard/DashboardActionStrip.svelte';
	import PatientShell from '$lib/components/patient-dashboard/PatientShell.svelte';
	import api from '$lib/api.js';
	import { locale, localeText } from '$lib/i18n';
	import { clearUser, user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let saving = false;
	let error = '';
	let success = '';
	let profile = {
		email: '',
		full_name: '',
		date_of_birth: '',
		diagnosis: '',
		consent_to_share: false
	};
	let assignedDoctor = null;
	let prescriptionSummary = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	$: header = {
		brand: 'NeuroBloom',
		title: lt('Profile', 'প্রোফাইল'),
		subtitle: currentUser?.full_name || currentUser?.email || lt('Patient', 'রোগী'),
		description: lt(
			'Keep your personal details and care information current in one calmer place.',
			'আপনার ব্যক্তিগত তথ্য ও কেয়ার-সংক্রান্ত তথ্য এক শান্ত জায়গা থেকে হালনাগাদ রাখুন।'
		),
		logoutLabel: lt('Logout', 'লগআউট')
	};

	$: headerActions = [
		{ label: lt('Notifications', 'নোটিফিকেশন'), href: '/notifications' },
		{ label: lt('Messages', 'বার্তা'), href: '/messages' },
		{ label: lt('Settings', 'সেটিংস'), href: '/settings' },
		{ type: 'logout', label: lt('Logout', 'লগআউট') }
	];

	$: quickLinks = [
		{
			label: lt('Progress', 'অগ্রগতি'),
			href: '/progress',
			eyebrow: lt('Recovery view', 'রেকভারি ভিউ'),
			description: lt('See your overview, domains, and history.', 'ওভারভিউ, ডোমেইন ও হিস্ট্রি দেখুন।')
		},
		{
			label: lt('Insights', 'ইনসাইট'),
			href: '/progress/insights',
			eyebrow: lt('Advanced view', 'উন্নত ভিউ'),
			description: lt('Open biomarkers and check-in trends.', 'বায়োমার্কার ও চেক-ইন ট্রেন্ড খুলুন।')
		},
		{
			label: lt('Prescriptions', 'প্রেসক্রিপশন'),
			href: '/prescriptions',
			eyebrow: lt('Care access', 'কেয়ার অ্যাক্সেস'),
			description: lt('Review doctor-issued plans and medication notes.', 'চিকিৎসকের দেওয়া পরিকল্পনা ও ওষুধের নোট দেখুন।')
		},
		{
			label: assignedDoctor ? lt('Doctor connected', 'ডাক্তার যুক্ত') : lt('Find doctor', 'ডাক্তার খুঁজুন'),
			href: '/find-doctor',
			eyebrow: lt('Support', 'সহায়তা'),
			description: assignedDoctor
				? lt('Browse or manage your care connection.', 'আপনার কেয়ার সংযোগ দেখুন বা পরিচালনা করুন।')
				: lt('Connect with a clinician when you need guided support.', 'নির্দেশিত সহায়তা দরকার হলে চিকিৎসকের সঙ্গে যুক্ত হোন।')
		}
	];

	onMount(async () => {
		if (!currentUser || currentUser.role !== 'patient') {
			goto('/login');
			return;
		}

		await loadProfileWorkspace();
	});

	async function loadProfileWorkspace() {
		loading = true;
		error = '';

		try {
			const [profileResponse, doctorResponse, prescriptionsResponse] = await Promise.allSettled([
				api.get(`/api/auth/patient/${currentUser.id}/profile`),
				api.get(`/api/doctor/patient/${currentUser.id}/assigned-doctor`),
				api.get(`/api/auth/patient/${currentUser.id}/prescriptions`)
			]);

			if (profileResponse.status === 'fulfilled') {
				profile = {
					...profile,
					...profileResponse.value.data
				};
			} else {
				throw profileResponse.reason;
			}

			assignedDoctor = doctorResponse.status === 'fulfilled' ? doctorResponse.value.data : null;
			prescriptionSummary =
				prescriptionsResponse.status === 'fulfilled' ? prescriptionsResponse.value.data : null;
		} catch (loadError) {
			console.error('Failed to load profile workspace:', loadError);
			error = lt('We could not load your profile right now.', 'এই মুহূর্তে আপনার প্রোফাইল লোড করা যায়নি।');
		} finally {
			loading = false;
		}
	}

	async function saveProfile() {
		saving = true;
		error = '';
		success = '';

		try {
			await api.patch(`/api/auth/patient/${currentUser.id}/profile`, null, {
				params: {
					full_name: profile.full_name || '',
					date_of_birth: profile.date_of_birth || '',
					diagnosis: profile.diagnosis || ''
				}
			});

			success = lt('Your profile has been updated.', 'আপনার প্রোফাইল হালনাগাদ হয়েছে।');
		} catch (saveError) {
			console.error('Failed to save profile:', saveError);
			error =
				saveError.response?.data?.detail ||
				lt('We could not save your profile.', 'আপনার প্রোফাইল সংরক্ষণ করা যায়নি।');
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
		<section class="hero-card">
			<div>
				<p class="eyebrow">{lt('Patient profile', 'রোগীর প্রোফাইল')}</p>
				<h2>{lt('Your identity, diagnosis, and care details all live here.', 'আপনার পরিচয়, ডায়াগনোসিস ও কেয়ার-সংক্রান্ত তথ্য এখানে একসঙ্গে আছে।')}</h2>
				<p class="description">{lt('Keep these details current so your care team and patient workspace stay aligned.', 'এই তথ্যগুলো হালনাগাদ রাখলে আপনার কেয়ার টিম ও রোগী ওয়ার্কস্পেস আরও সঠিকভাবে কাজ করবে।')}</p>
			</div>
			<div class="status-chip">
				<span>{lt('Care sharing', 'ডেটা শেয়ারিং')}</span>
				<strong>{profile.consent_to_share ? lt('Enabled', 'সক্রিয়') : lt('Disabled', 'নিষ্ক্রিয়')}</strong>
			</div>
		</section>

		<DashboardActionStrip actions={quickLinks} />
	</div>

	<div slot="rail" class="page-stack">
		<section class="panel-card">
			<p class="eyebrow">{lt('Care summary', 'কেয়ার সারাংশ')}</p>
			<h3>{assignedDoctor?.assigned ? assignedDoctor.doctor?.full_name : lt('No doctor assigned yet', 'এখনো কোনো ডাক্তার নির্ধারিত হয়নি')}</h3>
			<p class="muted">
				{#if assignedDoctor?.assigned}
					{assignedDoctor.doctor?.specialization}
					{#if assignedDoctor.doctor?.institution}
						· {assignedDoctor.doctor.institution}
					{/if}
				{:else}
					{lt('You can keep training independently or browse doctors whenever you want guided support.', 'আপনি স্বাধীনভাবে ট্রেনিং চালিয়ে যেতে পারেন, অথবা নির্দেশিত সহায়তা চাইলে ডাক্তার খুঁজে নিতে পারেন।')}
				{/if}
			</p>
			<div class="summary-list">
				<div>
					<span>{lt('Email', 'ইমেইল')}</span>
					<strong>{profile.email || currentUser?.email}</strong>
				</div>
				<div>
					<span>{lt('Active prescriptions', 'সক্রিয় প্রেসক্রিপশন')}</span>
					<strong>{prescriptionSummary?.summary?.active || 0}</strong>
				</div>
			</div>
		</section>
	</div>

	<div slot="main-bottom" class="page-stack">
		<section class="panel-card">
			<div class="section-head">
				<div>
					<p class="eyebrow">{lt('Editable details', 'সম্পাদনাযোগ্য তথ্য')}</p>
					<h3>{lt('Update your patient information', 'আপনার রোগী-তথ্য হালনাগাদ করুন')}</h3>
				</div>
				<button class="primary-btn" on:click={saveProfile} disabled={saving || loading}>
					{saving ? lt('Saving...', 'সংরক্ষণ হচ্ছে...') : lt('Save changes', 'পরিবর্তন সংরক্ষণ করুন')}
				</button>
			</div>

			{#if loading}
				<p class="muted">{lt('Loading your profile...', 'আপনার প্রোফাইল লোড হচ্ছে...')}</p>
			{:else}
				<div class="form-grid">
					<label>
						<span>{lt('Full name', 'পূর্ণ নাম')}</span>
						<input bind:value={profile.full_name} placeholder={lt('Enter your full name', 'আপনার পূর্ণ নাম লিখুন')} />
					</label>

					<label>
						<span>{lt('Date of birth', 'জন্মতারিখ')}</span>
						<input bind:value={profile.date_of_birth} type="date" />
					</label>

					<label class="full-width">
						<span>{lt('Diagnosis', 'ডায়াগনোসিস')}</span>
						<textarea bind:value={profile.diagnosis} rows="4" placeholder={lt('Describe your diagnosis or leave this for later', 'আপনার ডায়াগনোসিস লিখুন অথবা পরে পূরণ করুন')}></textarea>
					</label>
				</div>
			{/if}

			{#if success}
				<p class="success">{success}</p>
			{/if}
		</section>

		<section class="panel-card">
			<p class="eyebrow">{lt('Profile notes', 'প্রোফাইল নোট')}</p>
			<div class="summary-list expanded">
				<div>
					<span>{lt('Connected support', 'সংযুক্ত সহায়তা')}</span>
					<strong>{assignedDoctor?.assigned ? lt('Clinician linked', 'চিকিৎসক যুক্ত') : lt('Independent mode', 'স্বতন্ত্র মোড')}</strong>
				</div>
				<div>
					<span>{lt('Privacy controls', 'গোপনীয়তা নিয়ন্ত্রণ')}</span>
					<strong>{lt('Move to settings for consent and language', 'কনসেন্ট ও ভাষার জন্য সেটিংসে যান')}</strong>
				</div>
			</div>
		</section>
	</div>
</PatientShell>

<style>
	.page-stack {
		display: grid;
		gap: 1rem;
	}

	.hero-card,
	.panel-card {
		padding: 1.25rem;
		border-radius: 24px;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(203, 213, 225, 0.76);
		box-shadow: 0 16px 32px rgba(15, 23, 42, 0.05);
	}

	.hero-card {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		background: linear-gradient(135deg, rgba(240, 249, 255, 0.96), rgba(255, 255, 255, 0.92));
	}

	.eyebrow,
	h2,
	h3,
	.description,
	.muted,
	.success,
	.status-chip span,
	.status-chip strong {
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
		font-size: clamp(1.6rem, 3vw, 2.2rem);
		line-height: 1.15;
		color: #0f172a;
		max-width: 24ch;
	}

	h3 {
		margin-top: 0.25rem;
		font-size: 1.25rem;
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

	.status-chip {
		padding: 0.9rem 1rem;
		border-radius: 18px;
		background: rgba(248, 250, 252, 0.92);
		border: 1px solid rgba(203, 213, 225, 0.74);
		display: grid;
		gap: 0.25rem;
		min-width: 180px;
	}

	.status-chip span {
		font-size: 0.78rem;
		font-weight: 700;
		color: #64748b;
	}

	.status-chip strong {
		font-size: 1rem;
		color: #0f172a;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.full-width {
		grid-column: 1 / -1;
	}

	label {
		display: grid;
		gap: 0.45rem;
	}

	label span {
		font-size: 0.88rem;
		font-weight: 700;
		color: #334155;
	}

	input,
	textarea {
		width: 100%;
		padding: 0.85rem 0.95rem;
		border-radius: 16px;
		border: 1px solid rgba(203, 213, 225, 0.9);
		background: #f8fafc;
		font: inherit;
		color: #0f172a;
		box-sizing: border-box;
	}

	textarea {
		resize: vertical;
	}

	.primary-btn {
		border: none;
		border-radius: 999px;
		padding: 0.85rem 1.15rem;
		background: linear-gradient(135deg, #0f766e, #0ea5a4);
		color: #fff;
		font-weight: 800;
		cursor: pointer;
	}

	.primary-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.summary-list {
		display: grid;
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.summary-list.expanded {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.summary-list div {
		padding: 0.9rem 1rem;
		border-radius: 18px;
		background: #f8fafc;
		border: 1px solid rgba(203, 213, 225, 0.72);
		display: grid;
		gap: 0.2rem;
	}

	.summary-list span {
		font-size: 0.82rem;
		color: #64748b;
	}

	.summary-list strong {
		font-size: 0.98rem;
		color: #0f172a;
	}

	.success {
		margin-top: 0.9rem;
		color: #047857;
		font-weight: 700;
	}

	@media (max-width: 900px) {
		.hero-card,
		.section-head {
			flex-direction: column;
		}

		.form-grid,
		.summary-list.expanded {
			grid-template-columns: 1fr;
		}
	}
</style>
