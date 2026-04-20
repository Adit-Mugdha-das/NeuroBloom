<script>
	import { goto } from '$app/navigation';
	import api, { API_BASE_URL } from '$lib/api.js';
	import { locale, localeText } from '$lib/i18n';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = '';
	let prescriptionData = null;

	const unsubscribe = user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	onMount(() => {
		if (!currentUser) {
			goto('/login');
			return unsubscribe;
		}

		loadPrescriptions();

		return unsubscribe;
	});

	async function loadPrescriptions() {
		loading = true;
		error = '';

		try {
			const response = await api.get(`/api/auth/patient/${currentUser.id}/prescriptions`);
			prescriptionData = response.data;
		} catch (requestError) {
			error =
				requestError.response?.data?.detail ||
				lt('Failed to load prescriptions.', 'প্রেসক্রিপশন লোড করা যায়নি।');
		} finally {
			loading = false;
		}
	}

	function formatDate(dateValue) {
		if (!dateValue) return lt('Not scheduled', 'নির্ধারিত নয়');
		return new Date(dateValue).toLocaleDateString($locale === 'bn' ? 'bn-BD' : 'en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function formatDateTime(dateValue) {
		if (!dateValue) return lt('Not available', 'পাওয়া যায়নি');
		return new Date(dateValue).toLocaleString($locale === 'bn' ? 'bn-BD' : 'en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function viewPdf(prescription) {
		window.open(
			`${API_BASE_URL}/api/auth/patient/${currentUser.id}/prescriptions/${prescription.id}/pdf`,
			'_blank',
			'noopener'
		);
	}

	async function downloadPdf(prescription) {
		try {
			const response = await api.get(
				`/api/auth/patient/${currentUser.id}/prescriptions/${prescription.id}/pdf`,
				{ responseType: 'blob' }
			);
			const blob = new Blob([response.data], { type: 'application/pdf' });
			const url = window.URL.createObjectURL(blob);
			const anchor = document.createElement('a');
			anchor.href = url;
			anchor.download = `prescription-${prescription.verification_id}.pdf`;
			document.body.appendChild(anchor);
			anchor.click();
			anchor.remove();
			window.URL.revokeObjectURL(url);
		} catch (requestError) {
			error =
				requestError.response?.data?.detail ||
				lt('Failed to download the prescription PDF.', 'প্রেসক্রিপশনের PDF ডাউনলোড করা যায়নি।');
		}
	}

	function translateStatus(status) {
		const normalized = String(status || '').replaceAll('_', ' ');
		if ($locale !== 'bn') return normalized;
		if (normalized === 'active') return 'সক্রিয়';
		if (normalized === 'revised') return 'সংশোধিত';
		if (normalized === 'inactive') return 'নিষ্ক্রিয়';
		return normalized;
	}

	$: latestPrescription = prescriptionData?.prescriptions?.[0] || null;
	$: overviewCards = prescriptionData
		? [
				{
					label: lt('Total prescriptions', 'মোট প্রেসক্রিপশন'),
					value: prescriptionData.summary?.total || 0
				},
				{
					label: lt('Active prescriptions', 'সক্রিয় প্রেসক্রিপশন'),
					value: prescriptionData.summary?.active || 0
				},
				{
					label: lt('Treating doctor', 'চিকিৎসক'),
					value: prescriptionData.doctor?.name || lt('Not assigned', 'নির্ধারিত নয়')
				},
				{
					label: lt('Latest issued', 'সর্বশেষ ইস্যু'),
					value: latestPrescription ? formatDate(latestPrescription.created_at) : lt('Not available', 'পাওয়া যায়নি')
				}
			]
		: [];
</script>

<div class="page-shell">
	<header class="topbar">
		<div>
			<p class="eyebrow">NeuroBloom</p>
			<h1>{lt('My Prescriptions', 'আমার প্রেসক্রিপশন')}</h1>
			<p class="subcopy">{lt('Your clinician-issued care plans live here, with quick access to the latest PDF and a calmer history view.', 'চিকিৎসকের দেওয়া কেয়ার প্ল্যানগুলো এখানে থাকবে, সঙ্গে থাকবে সর্বশেষ PDF ও একটি শান্ত ইতিহাস ভিউ।')}</p>
		</div>
		<div class="header-actions">
			<button class="ghost-btn" on:click={() => goto('/dashboard')}>{lt('Back to dashboard', 'ড্যাশবোর্ডে ফিরুন')}</button>
			<button class="ghost-btn" on:click={() => goto('/messages')}>{lt('Messages', 'বার্তা')}</button>
			<button class="ghost-btn" on:click={() => goto('/profile')}>{lt('Profile', 'প্রোফাইল')}</button>
		</div>
	</header>

	<main class="page-main">
		{#if loading}
			<section class="state-card"><p>{lt('Loading prescriptions...', 'প্রেসক্রিপশন লোড হচ্ছে...')}</p></section>
		{:else if error}
			<section class="state-card error-state"><p>{error}</p></section>
		{:else if !prescriptionData?.has_doctor}
			<section class="empty-card">
				<h2>{lt('No assigned doctor yet', 'এখনো কোনো ডাক্তার নির্ধারিত হয়নি')}</h2>
				<p>{lt('Once a treating clinician is assigned and issues a prescription, it will appear here automatically.', 'চিকিৎসক নির্ধারিত হলে এবং প্রেসক্রিপশন দিলে তা এখানে দেখা যাবে।')}</p>
				<button class="primary-btn" on:click={() => goto('/find-doctor')}>{lt('Find a doctor', 'ডাক্তার খুঁজুন')}</button>
			</section>
		{:else}
			<section class="overview-grid">
				{#each overviewCards as card}
					<article class="overview-card">
						<p>{card.label}</p>
						<strong>{card.value}</strong>
					</article>
				{/each}
			</section>

			<section class="hero-card">
				<div>
					<p class="section-kicker">{lt('Care summary', 'কেয়ার সারাংশ')}</p>
					<h2>{prescriptionData.doctor?.name || lt('Assigned doctor', 'নির্ধারিত ডাক্তার')}</h2>
					<p class="hero-copy">
						{#if latestPrescription}
							<span>{lt('Latest prescription:', 'সর্বশেষ প্রেসক্রিপশন:')}</span>
							<span data-localize-skip> {latestPrescription.title}</span>
							<span>{lt('Review the PDF for the full medication and instructions list.', 'পূর্ণ ওষুধ ও নির্দেশনার তালিকা দেখতে PDF খুলুন।')}</span>
						{:else}
							{lt('Your clinician is connected. New prescriptions will appear here.', 'আপনার চিকিৎসক সংযুক্ত আছেন। নতুন প্রেসক্রিপশন এখানে দেখা যাবে।')}
						{/if}
					</p>
				</div>
				{#if latestPrescription}
					<div class="hero-actions">
						<button class="ghost-btn" on:click={() => viewPdf(latestPrescription)}>{lt('View latest PDF', 'সর্বশেষ PDF দেখুন')}</button>
						<button class="primary-btn" on:click={() => downloadPdf(latestPrescription)}>{lt('Download latest', 'সর্বশেষটি ডাউনলোড করুন')}</button>
					</div>
				{/if}
			</section>

			<section class="history-card">
				<div class="section-head">
					<div>
						<p class="section-kicker">{lt('Prescription history', 'প্রেসক্রিপশন ইতিহাস')}</p>
						<h2>{lt('Issued documents', 'ইস্যু করা নথি')}</h2>
					</div>
					<span class="meta-pill">{prescriptionData.prescriptions.length} {lt('total', 'মোট')}</span>
				</div>

				{#if !prescriptionData.prescriptions.length}
					<div class="empty-card inline-empty">
						<p>{lt('No prescriptions have been issued yet.', 'এখনো কোনো প্রেসক্রিপশন দেওয়া হয়নি।')}</p>
					</div>
				{:else}
					<div class="prescription-list">
						{#each prescriptionData.prescriptions as prescription}
							<article class="prescription-card">
								<div class="card-head">
									<div>
										<p class="card-kicker">{prescription.verification_id}</p>
										<h3 data-localize-skip>{prescription.title}</h3>
										<p class="summary-copy" data-localize-skip>{prescription.summary || prescription.patient_instructions}</p>
									</div>
									<div class="card-meta">
										<span class="status-pill status-{prescription.status}">{translateStatus(prescription.status)}</span>
										<span>{lt('Version', 'সংস্করণ')} {prescription.version_number}</span>
										<span>{formatDateTime(prescription.created_at)}</span>
									</div>
								</div>

								<div class="detail-grid">
									<div><span>{lt('Doctor', 'ডাক্তার')}</span><strong data-localize-skip>{prescription.doctor_name}</strong></div>
									<div><span>{lt('Review date', 'রিভিউ তারিখ')}</span><strong>{formatDate(prescription.review_date)}</strong></div>
									<div><span>{lt('Valid until', 'কার্যকর থাকবে')}</span><strong>{formatDate(prescription.valid_until)}</strong></div>
									<div><span>{lt('Medication count', 'ওষুধের সংখ্যা')}</span><strong>{prescription.medication_count}</strong></div>
								</div>

								{#if prescription.medications?.length}
									<div class="medication-list">
										{#each prescription.medications as medication}
											<div class="medication-item" data-localize-skip>
												<strong>{medication.name}</strong>
												<span>{medication.dosage} · {medication.frequency}{medication.duration ? ` · ${medication.duration}` : ''}</span>
												{#if medication.instructions}
													<small>{medication.instructions}</small>
												{/if}
											</div>
										{/each}
									</div>
								{/if}

								{#if prescription.lifestyle_plan?.length}
									<div class="support-block">
										<p class="card-kicker">{lt('Lifestyle recommendations', 'জীবনযাপন-সংক্রান্ত পরামর্শ')}</p>
										<ul data-localize-skip>
											{#each prescription.lifestyle_plan as item}
												<li>{item}</li>
											{/each}
										</ul>
									</div>
								{/if}

								<div class="action-row">
									<button class="ghost-btn" on:click={() => viewPdf(prescription)}>{lt('View PDF', 'PDF দেখুন')}</button>
									<button class="primary-btn" on:click={() => downloadPdf(prescription)}>{lt('Download', 'ডাউনলোড')}</button>
								</div>
							</article>
						{/each}
					</div>
				{/if}
			</section>
		{/if}
	</main>
</div>

<style>
	:global(body) {
		background: linear-gradient(135deg, #eef2ff, #e0f7f4);
	}

	.page-shell {
		min-height: 100vh;
		background:
			radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 28%),
			radial-gradient(circle at top right, rgba(79, 70, 229, 0.12), transparent 24%),
			linear-gradient(135deg, #eef2ff, #e0f7f4);
		padding: 1.5rem;
	}

	.topbar,
	.state-card,
	.empty-card,
	.overview-card,
	.hero-card,
	.history-card,
	.prescription-card {
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.7);
		border-radius: 24px;
		box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
	}

	.topbar,
	.hero-card,
	.history-card,
	.state-card,
	.empty-card {
		padding: 1.25rem;
	}

	.topbar {
		max-width: 1180px;
		margin: 0 auto 1rem;
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.eyebrow,
	.section-kicker,
	.card-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #0f766e;
	}

	h1,
	h2,
	h3 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.subcopy,
	.hero-copy,
	.summary-copy,
	.state-card p,
	.empty-card p,
	.support-block li,
	.medication-item span,
	.medication-item small {
		color: #6b7280;
		line-height: 1.58;
	}

	.header-actions,
	.action-row,
	.section-head,
	.card-head,
	.card-meta,
	.hero-actions {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.section-head,
	.card-head {
		justify-content: space-between;
		align-items: flex-start;
	}

	.card-meta {
		justify-content: flex-end;
		color: #6b7280;
		font-size: 0.84rem;
	}

	.page-main,
	.overview-grid,
	.prescription-list,
	.detail-grid,
	.medication-list {
		display: grid;
		gap: 1rem;
	}

	.page-main {
		max-width: 1180px;
		margin: 0 auto;
	}

	.overview-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.overview-card {
		padding: 1rem;
	}

	.overview-card p,
	.detail-grid span {
		margin: 0;
		font-size: 0.84rem;
		color: #6b7280;
	}

	.overview-card strong,
	.detail-grid strong {
		display: block;
		margin-top: 0.3rem;
		color: #111827;
	}

	.hero-card {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
		background: linear-gradient(135deg, rgba(15, 118, 110, 0.08), rgba(79, 70, 229, 0.08));
	}

	.history-card {
		display: grid;
		gap: 1rem;
	}

	.meta-pill,
	.status-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.38rem 0.75rem;
		border-radius: 999px;
		font-size: 0.78rem;
		font-weight: 800;
	}

	.meta-pill {
		background: #ecfeff;
		color: #0f766e;
	}

	.status-pill.status-active {
		background: #dcfce7;
		color: #166534;
	}

	.status-pill.status-revised,
	.status-pill.status-inactive {
		background: #e5e7eb;
		color: #4b5563;
	}

	.prescription-card {
		padding: 1.15rem;
		display: grid;
		gap: 1rem;
	}

	.detail-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.detail-grid div,
	.medication-item,
	.support-block,
	.inline-empty {
		padding: 0.95rem;
		border-radius: 18px;
		background: #f8fafc;
	}

	.support-block ul {
		margin: 0.65rem 0 0;
		padding-left: 1rem;
	}

	.ghost-btn,
	.primary-btn {
		border-radius: 999px;
		padding: 0.78rem 1rem;
		font-weight: 700;
		cursor: pointer;
	}

	.ghost-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	.primary-btn {
		border: 1px solid #0f766e;
		background: linear-gradient(135deg, #0f766e, #0ea5a4);
		color: #ffffff;
	}

	@media (max-width: 1024px) {
		.overview-grid,
		.detail-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.page-shell {
			padding: 1rem;
		}

		.topbar,
		.hero-card,
		.section-head,
		.card-head {
			flex-direction: column;
		}

		.overview-grid,
		.detail-grid {
			grid-template-columns: 1fr;
		}

		.card-meta {
			justify-content: flex-start;
		}
	}
</style>
