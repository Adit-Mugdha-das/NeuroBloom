<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api, { API_BASE_URL } from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let patientId;
	let userData;
	let patient = null;
	let prescriptions = [];
	let summary = { total: 0, active: 0 };
	let loading = true;
	let saving = false;
	let error = '';
	let formError = '';
	let showComposer = false;
	let editingPrescription = null;
	let statusUpdatingId = null;

	const unsubscribeUser = user.subscribe((value) => {
		userData = value;
	});

	const unsubscribePage = page.subscribe((value) => {
		patientId = value.params.id;
	});

	function createMedication() {
		return {
			name: '',
			dosage: '',
			frequency: '',
			duration: '',
			instructions: ''
		};
	}

	function createDraft() {
		return {
			title: '',
			summary: '',
			patient_instructions: '',
			clinician_notes: '',
			follow_up_plan: '',
			status: 'active',
			valid_until: '',
			review_date: '',
			lifestyle_plan_text: '',
			medications: [createMedication()]
		};
	}

	let draft = createDraft();

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadPrescriptions();

		return () => {
			unsubscribeUser();
			unsubscribePage();
		};
	});

	async function loadPrescriptions() {
		loading = true;
		error = '';

		try {
			const response = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/prescriptions`);
			patient = response.data.patient;
			prescriptions = response.data.prescriptions || [];
			summary = response.data.summary || { total: 0, active: 0 };
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load prescriptions';
		} finally {
			loading = false;
		}
	}

	function openCreateComposer() {
		editingPrescription = null;
		draft = createDraft();
		formError = '';
		showComposer = true;
	}

	function openRevisionComposer(prescription) {
		editingPrescription = prescription;
		draft = {
			title: prescription.title || '',
			summary: prescription.summary || '',
			patient_instructions: prescription.patient_instructions || '',
			clinician_notes: prescription.clinician_notes || '',
			follow_up_plan: prescription.follow_up_plan || '',
			status: 'active',
			valid_until: prescription.valid_until ? prescription.valid_until.slice(0, 10) : '',
			review_date: prescription.review_date ? prescription.review_date.slice(0, 10) : '',
			lifestyle_plan_text: (prescription.lifestyle_plan || []).join('\n'),
			medications: (prescription.medications || []).length
				? prescription.medications.map((item) => ({
					name: item.name || '',
					dosage: item.dosage || '',
					frequency: item.frequency || '',
					duration: item.duration || '',
					instructions: item.instructions || ''
				}))
				: [createMedication()]
		};
		formError = '';
		showComposer = true;
	}

	function closeComposer() {
		showComposer = false;
		editingPrescription = null;
		formError = '';
	}

	function addMedication() {
		draft = {
			...draft,
			medications: [...draft.medications, createMedication()]
		};
	}

	function removeMedication(index) {
		const medications = draft.medications.filter((_, itemIndex) => itemIndex !== index);
		draft = {
			...draft,
			medications: medications.length ? medications : [createMedication()]
		};
	}

	function updateMedication(index, field, value) {
		const medications = draft.medications.map((item, itemIndex) => {
			if (itemIndex !== index) return item;
			return { ...item, [field]: value };
		});

		draft = { ...draft, medications };
	}

	function buildPayload() {
		const medications = draft.medications
			.map((item) => ({
				name: item.name.trim(),
				dosage: item.dosage.trim(),
				frequency: item.frequency.trim(),
				duration: item.duration.trim() || null,
				instructions: item.instructions.trim() || null
			}))
			.filter((item) => item.name && item.dosage && item.frequency);

		return {
			title: draft.title.trim(),
			summary: draft.summary.trim() || null,
			patient_instructions: draft.patient_instructions.trim(),
			clinician_notes: draft.clinician_notes.trim() || null,
			follow_up_plan: draft.follow_up_plan.trim() || null,
			status: draft.status,
			valid_until: draft.valid_until || null,
			review_date: draft.review_date || null,
			lifestyle_plan: draft.lifestyle_plan_text
				.split('\n')
				.map((item) => item.trim())
				.filter(Boolean),
			medications
		};
	}

	async function savePrescription() {
		formError = '';
		const payload = buildPayload();

		if (!payload.title) {
			formError = 'Prescription title is required.';
			return;
		}

		if (!payload.patient_instructions) {
			formError = 'Patient instructions are required.';
			return;
		}

		if (!payload.medications.length && !payload.lifestyle_plan.length) {
			formError = 'Add at least one medication or one lifestyle recommendation.';
			return;
		}

		saving = true;
		try {
			if (editingPrescription) {
				await api.put(`/api/doctor/${userData.id}/patient/${patientId}/prescriptions/${editingPrescription.id}`, payload);
			} else {
				await api.post(`/api/doctor/${userData.id}/patient/${patientId}/prescriptions`, payload);
			}

			closeComposer();
			await loadPrescriptions();
		} catch (requestError) {
			formError = requestError.response?.data?.detail || 'Failed to save prescription';
		} finally {
			saving = false;
		}
	}

	function openPdf(prescription) {
		window.open(`${API_BASE_URL}/api/doctor/${userData.id}/patient/${patientId}/prescriptions/${prescription.id}/pdf`, '_blank', 'noopener');
	}

	async function downloadPdf(prescription) {
		try {
			const response = await api.get(
				`/api/doctor/${userData.id}/patient/${patientId}/prescriptions/${prescription.id}/pdf`,
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
			formError = requestError.response?.data?.detail || 'Failed to download prescription PDF';
		}
	}

	async function updatePrescriptionStatus(prescription, nextStatus) {
		const reason = nextStatus === 'active'
			? 'Prescription reactivated by treating doctor.'
			: window.prompt('Reason for deactivating this prescription?', 'Superseded by a new plan') || '';

		if (nextStatus !== 'active' && !reason.trim()) {
			formError = 'A reason is required to deactivate a prescription.';
			return;
		}

		statusUpdatingId = prescription.id;
		formError = '';

		try {
			await api.patch(
				`/api/doctor/${userData.id}/patient/${patientId}/prescriptions/${prescription.id}/status`,
				{ status: nextStatus, reason: reason.trim() || null }
			);
			await loadPrescriptions();
		} catch (requestError) {
			formError = requestError.response?.data?.detail || 'Failed to update prescription status';
		} finally {
			statusUpdatingId = null;
		}
	}

	function formatDate(dateValue) {
		if (!dateValue) return 'Not scheduled';
		return new Date(dateValue).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function formatDateTime(dateValue) {
		if (!dateValue) return 'Not available';
		return new Date(dateValue).toLocaleString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function handleOverlayKeydown(event) {
		if (event.key === 'Enter' || event.key === ' ' || event.key === 'Escape') {
			event.preventDefault();
			closeComposer();
		}
	}

	$: previewMedications = draft.medications
		.map((item) => ({ ...item, name: item.name.trim(), dosage: item.dosage.trim(), frequency: item.frequency.trim() }))
		.filter((item) => item.name || item.dosage || item.frequency || item.duration || item.instructions);
	$: previewLifestyleItems = draft.lifestyle_plan_text.split('\n').map((item) => item.trim()).filter(Boolean);
	$: patientName = patient?.full_name || patient?.email || 'Patient';
	$: latestActivePrescription = prescriptions.find((prescription) => prescription.status === 'active') || null;
	$: heroCards = [
		{ label: 'Total Prescriptions', value: summary.total },
		{ label: 'Active', value: summary.active },
		{ label: 'Latest Review', value: latestActivePrescription?.review_date ? formatDate(latestActivePrescription.review_date) : 'Not scheduled' },
		{ label: 'Diagnosis', value: patient?.diagnosis || 'Not recorded' }
	];
</script>

<DoctorWorkspaceShell
	title={`Prescriptions · ${patientName}`}
	subtitle={uiText("Structured digital prescribing with revision history, clinician review, PDF generation, and patient delivery.", $activeLocale)}
	eyebrow="Doctor Patient Workspace"
	maxWidth="1360px"
>
	<svelte:fragment slot="actions">
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}`)}>Patient Overview</button>
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}/reports`)}>Reports</button>
		<button class="primary-btn" on:click={openCreateComposer}>Create Prescription</button>
	</svelte:fragment>

	{#if loading}
		<section class="state-card"><p>{uiText("Loading prescriptions...", $activeLocale)}</p></section>
	{:else if error}
		<section class="state-card error-state"><p>{error}</p></section>
	{:else}
		<section class="hero-card">
			<div>
				<p class="eyebrow-copy">{uiText("Patient Prescription Record", $activeLocale)}</p>
				<h2>{patientName}</h2>
				<p class="hero-copy" data-localize-skip>{patient?.diagnosis || patient?.treatment_goal || 'No diagnosis or treatment goal recorded yet.'}</p>
				{#if latestActivePrescription}
					<p class="hero-note">{uiText("Current active prescription:", $activeLocale)} {latestActivePrescription.title} · {latestActivePrescription.verification_id}</p>
				{/if}
			</div>
			<div class="hero-grid">
				{#each heroCards as card}
					<div class="hero-metric">
						<span>{card.label}</span>
						{#if card.label === 'Diagnosis'}
							<strong data-localize-skip>{card.value}</strong>
						{:else}
							<strong>{card.value}</strong>
						{/if}
					</div>
				{/each}
			</div>
		</section>

		<section class="panel-card section-card">
			<div class="section-head">
				<div>
					<p class="section-kicker">{uiText("Prescription History", $activeLocale)}</p>
					<h3>{uiText("Issued documents and revisions", $activeLocale)}</h3>
				</div>
				<span class="meta-pill">{prescriptions.length} {uiText("record", $activeLocale)}{prescriptions.length === 1 ? '' : 's'}</span>
			</div>

			{#if prescriptions.length === 0}
				<div class="empty-state">
					<h3>{uiText("No prescriptions have been issued yet", $activeLocale)}</h3>
					<p>{uiText("Create the first structured prescription to add it to the patient’s history and deliver it through the patient portal.", $activeLocale)}</p>
					<button class="primary-btn" on:click={openCreateComposer}>{uiText("Create First Prescription", $activeLocale)}</button>
				</div>
			{:else}
				{#if formError}
					<p class="form-error inline-error">{formError}</p>
				{/if}
				<div class="prescription-list">
					{#each prescriptions as prescription}
						<article class="prescription-card">
							<div class="prescription-head">
								<div>
									<div class="head-row">
										<p class="card-kicker">{prescription.verification_id}</p>
										<span class="status-pill status-{prescription.status}">{prescription.status.replaceAll('_', ' ')}</span>
									</div>
									<h3 data-localize-skip>{prescription.title}</h3>
									<p class="summary-copy" data-localize-skip>{prescription.summary || prescription.patient_instructions}</p>
								</div>
								<div class="head-meta">
									<span>{uiText("Issued", $activeLocale)} {formatDateTime(prescription.created_at)}</span>
									<span>{uiText("Version", $activeLocale)} {prescription.version_number}</span>
								</div>
							</div>

							<div class="detail-grid">
								<div>
									<span>{uiText("Patient instructions", $activeLocale)}</span>
									<strong data-localize-skip>{prescription.patient_instructions}</strong>
								</div>
								<div>
									<span>{uiText("Review date", $activeLocale)}</span>
									<strong>{formatDate(prescription.review_date)}</strong>
								</div>
								<div>
									<span>{uiText("Valid until", $activeLocale)}</span>
									<strong>{formatDate(prescription.valid_until)}</strong>
								</div>
								<div>
									<span>{uiText("Medication count", $activeLocale)}</span>
									<strong>{prescription.medication_count}</strong>
								</div>
							</div>

							{#if prescription.retired_reason || prescription.retired_at}
								<div class="status-note-card">
									<p class="card-kicker">{uiText("Status Update", $activeLocale)}</p>
									<p>
										{#if prescription.retired_reason}
											<span data-localize-skip>{prescription.retired_reason}</span>
										{:else}
											{uiText("This prescription is no longer active.", $activeLocale)}
										{/if}
									</p>
									{#if prescription.retired_at}
										<small>{uiText("Updated", $activeLocale)} {formatDateTime(prescription.retired_at)}</small>
									{/if}
								</div>
							{/if}

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
								<div class="lifestyle-block">
									<p class="card-kicker">{uiText("Lifestyle Recommendations", $activeLocale)}</p>
									<ul data-localize-skip>
										{#each prescription.lifestyle_plan as item}
											<li>{item}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<div class="action-row">
								<button class="ghost-btn" on:click={() => openPdf(prescription)}>{uiText("View PDF", $activeLocale)}</button>
								<button class="ghost-btn" on:click={() => downloadPdf(prescription)}>{uiText("Download", $activeLocale)}</button>
								<button class="primary-btn" on:click={() => openRevisionComposer(prescription)}>{uiText("Edit And Reissue", $activeLocale)}</button>
								{#if prescription.status === 'active'}
									<button
										class="warning-btn"
										disabled={statusUpdatingId === prescription.id}
										on:click={() => updatePrescriptionStatus(prescription, 'inactive')}
									>
										{statusUpdatingId === prescription.id ? 'Updating...' : 'Deactivate'}
									</button>
								{:else}
									<button
										class="ghost-btn"
										disabled={statusUpdatingId === prescription.id}
										on:click={() => updatePrescriptionStatus(prescription, 'active')}
									>
										{statusUpdatingId === prescription.id ? 'Updating...' : 'Reactivate'}
									</button>
								{/if}
							</div>
						</article>
					{/each}
				</div>
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

{#if showComposer}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		aria-label={uiText("Close prescription composer", $activeLocale)}
		on:click={closeComposer}
		on:keydown={handleOverlayKeydown}
	>
		<div
			class="modal-shell"
			role="dialog"
			aria-modal="true"
			aria-label={uiText("Prescription composer", $activeLocale)}
			tabindex="-1"
			on:click|stopPropagation
			on:keydown|stopPropagation
		>
			<div class="modal-header">
				<div>
					<p class="section-kicker">{editingPrescription ? 'Revision' : 'New Prescription'}</p>
					<h2>{editingPrescription ? `Update ${editingPrescription.title}` : `Create prescription for ${patientName}`}</h2>
				</div>
				<button class="close-btn" on:click={closeComposer}>x</button>
			</div>

			<div class="composer-grid">
				<section class="composer-panel form-panel">
					<div class="form-grid">
						<label>
							<span>{uiText("Prescription title", $activeLocale)}</span>
							<input bind:value={draft.title} placeholder={uiText("Cognitive support medication plan", $activeLocale)} />
						</label>

						<label>
							<span>{uiText("Clinical summary", $activeLocale)}</span>
							<textarea bind:value={draft.summary} rows="3" placeholder={uiText("Short diagnostic and prescribing summary.", $activeLocale)}></textarea>
						</label>

						<label>
							<span>{uiText("Patient instructions", $activeLocale)}</span>
							<textarea bind:value={draft.patient_instructions} rows="4" placeholder={uiText("Explain how the patient should follow this plan.", $activeLocale)}></textarea>
						</label>

						<div class="two-up">
							<label>
								<span>{uiText("Valid until", $activeLocale)}</span>
								<input type="date" bind:value={draft.valid_until} />
							</label>
							<label>
								<span>{uiText("Review date", $activeLocale)}</span>
								<input type="date" bind:value={draft.review_date} />
							</label>
						</div>

						<label>
							<span>{uiText("Follow-up plan", $activeLocale)}</span>
							<textarea bind:value={draft.follow_up_plan} rows="2" placeholder={uiText("Follow-up review, monitoring, or lab instructions.", $activeLocale)}></textarea>
						</label>

						<label>
							<span>{uiText("Clinician notes", $activeLocale)}</span>
							<textarea bind:value={draft.clinician_notes} rows="3" placeholder={uiText("Private clinical notes to keep in the record.", $activeLocale)}></textarea>
						</label>

						<label>
							<span>{uiText("Lifestyle recommendations", $activeLocale)}</span>
							<textarea bind:value={draft.lifestyle_plan_text} rows="4" placeholder={uiText("One recommendation per line.", $activeLocale)}></textarea>
						</label>
					</div>

					<div class="medications-panel">
						<div class="section-head compact-head">
							<div>
								<p class="section-kicker">{uiText("Medication Items", $activeLocale)}</p>
								<h3>{uiText("Dosage, schedule, and duration", $activeLocale)}</h3>
							</div>
							<button class="ghost-btn" on:click={addMedication}>{uiText("Add Item", $activeLocale)}</button>
						</div>

						<div class="medication-editor-list">
							{#each draft.medications as medication, index}
								<div class="medication-editor">
									<div class="two-up">
										<label>
											<span>{uiText("Medication name", $activeLocale)}</span>
											<input value={medication.name} on:input={(event) => updateMedication(index, 'name', event.currentTarget.value)} placeholder={uiText("Donepezil", $activeLocale)} />
										</label>
										<label>
											<span>{uiText("Dosage", $activeLocale)}</span>
											<input value={medication.dosage} on:input={(event) => updateMedication(index, 'dosage', event.currentTarget.value)} placeholder={uiText("5 mg", $activeLocale)} />
										</label>
									</div>
									<div class="two-up">
										<label>
											<span>{uiText("Frequency", $activeLocale)}</span>
											<input value={medication.frequency} on:input={(event) => updateMedication(index, 'frequency', event.currentTarget.value)} placeholder={uiText("Once daily", $activeLocale)} />
										</label>
										<label>
											<span>{uiText("Duration", $activeLocale)}</span>
											<input value={medication.duration} on:input={(event) => updateMedication(index, 'duration', event.currentTarget.value)} placeholder={uiText("30 days", $activeLocale)} />
										</label>
									</div>
									<label>
										<span>{uiText("Instructions", $activeLocale)}</span>
										<input value={medication.instructions} on:input={(event) => updateMedication(index, 'instructions', event.currentTarget.value)} placeholder={uiText("Take after dinner", $activeLocale)} />
									</label>
									{#if draft.medications.length > 1}
										<button class="text-btn danger" on:click={() => removeMedication(index)}>{uiText("Remove item", $activeLocale)}</button>
									{/if}
								</div>
							{/each}
						</div>
					</div>

					{#if formError}
						<p class="form-error">{formError}</p>
					{/if}

					<div class="action-row composer-actions">
						<button class="ghost-btn" on:click={closeComposer}>{uiText("Cancel", $activeLocale)}</button>
						<button class="primary-btn" disabled={saving} on:click={savePrescription}>
							{saving ? 'Saving...' : editingPrescription ? 'Issue Revision' : 'Issue Prescription'}
						</button>
					</div>
				</section>

				<aside class="composer-panel preview-panel">
					<p class="section-kicker">{uiText("Live Review", $activeLocale)}</p>
					<h3>{draft.title || 'Prescription title preview'}</h3>
					<p class="preview-summary" data-localize-skip>{draft.summary || draft.patient_instructions || 'A short summary and patient-facing instructions will appear here as you compose the prescription.'}</p>

					<div class="preview-meta">
						<div><span>{uiText("Patient", $activeLocale)}</span><strong>{patientName}</strong></div>
						<div><span>{uiText("Diagnosis", $activeLocale)}</span><strong data-localize-skip>{patient?.diagnosis || 'Not recorded'}</strong></div>
						<div><span>{uiText("Review date", $activeLocale)}</span><strong>{draft.review_date || 'Not scheduled'}</strong></div>
						<div><span>{uiText("Status", $activeLocale)}</span><strong>{draft.status}</strong></div>
					</div>

					<div class="preview-block">
						<p class="card-kicker">{uiText("Medications", $activeLocale)}</p>
						{#if previewMedications.length}
							{#each previewMedications as medication}
								<div class="preview-item" data-localize-skip>
									<strong>{medication.name || 'Medication'}</strong>
									<span>{medication.dosage || '-'} · {medication.frequency || '-'}</span>
									{#if medication.duration}
										<small>{medication.duration}</small>
									{/if}
									{#if medication.instructions}
										<small>{medication.instructions}</small>
									{/if}
								</div>
							{/each}
						{:else}
							<p class="empty-copy">{uiText("Medication items will appear here.", $activeLocale)}</p>
						{/if}
					</div>

					<div class="preview-block">
						<p class="card-kicker">{uiText("Lifestyle Recommendations", $activeLocale)}</p>
						{#if previewLifestyleItems.length}
							<ul data-localize-skip>
								{#each previewLifestyleItems as item}
									<li>{item}</li>
								{/each}
							</ul>
						{:else}
							<p class="empty-copy">{uiText("Lifestyle guidance will appear here.", $activeLocale)}</p>
						{/if}
					</div>

					<div class="preview-block">
						<p class="card-kicker">{uiText("Patient Instructions", $activeLocale)}</p>
						<p data-localize-skip>{draft.patient_instructions || 'Patient-facing instructions will appear here.'}</p>
					</div>
				</aside>
			</div>
		</div>
	</div>
{/if}

<style>
	.hero-card,
	.panel-card,
	.state-card,
	.modal-shell,
	.composer-panel,
	.prescription-card,
	.hero-metric {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		border-radius: 24px;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.hero-card,
	.panel-card,
	.state-card,
	.modal-shell {
		padding: 1.25rem;
	}

	.hero-card {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 1rem;
		background: linear-gradient(135deg, #e0e7ff 0%, #eff6ff 100%);
	}

	.eyebrow-copy,
	.section-kicker,
	.card-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #0f766e;
	}

	h2,
	h3 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.hero-copy,
	.hero-note,
	.summary-copy,
	.empty-copy,
	.state-card p,
	.preview-summary,
	.lifestyle-block li,
	.preview-block li,
	.preview-block p {
		color: #6b7280;
	}

	.hero-grid,
	.detail-grid,
	.form-grid,
	.preview-meta,
	.composer-grid,
	.two-up {
		display: grid;
		gap: 1rem;
	}

	.hero-grid {
		grid-template-columns: repeat(2, minmax(180px, 1fr));
	}

	.hero-metric {
		padding: 0.9rem 1rem;
		background: rgba(255, 255, 255, 0.86);
	}

	.hero-metric span,
	.detail-grid span,
	.preview-meta span {
		font-size: 0.82rem;
		color: #6b7280;
	}

	.hero-metric strong,
	.detail-grid strong,
	.preview-meta strong {
		display: block;
		margin-top: 0.25rem;
		color: #111827;
	}

	.section-card {
		display: grid;
		gap: 1rem;
	}

	.section-head,
	.prescription-head,
	.action-row,
	.modal-header {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
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

	.empty-state {
		display: grid;
		gap: 0.8rem;
		padding: 1rem;
		border-radius: 20px;
		background: #f8fafc;
	}

	.prescription-list,
	.medication-list,
	.medication-editor-list {
		display: grid;
		gap: 1rem;
	}

	.prescription-card {
		padding: 1.15rem;
		display: grid;
		gap: 1rem;
	}

	.hero-note {
		margin: 0.75rem 0 0;
		font-weight: 700;
		color: #0f766e;
	}

	.head-row,
	.head-meta {
		display: flex;
		gap: 0.6rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.head-meta {
		justify-content: flex-end;
		color: #6b7280;
		font-size: 0.84rem;
	}

	.detail-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.detail-grid div,
	.preview-meta div {
		padding: 0.9rem;
		border-radius: 18px;
		background: #f8fafc;
	}

	.status-note-card {
		padding: 0.95rem 1rem;
		border-radius: 18px;
		background: #fff7ed;
		border: 1px solid #fed7aa;
	}

	.status-note-card p,
	.status-note-card small {
		margin: 0.35rem 0 0;
		color: #9a3412;
	}

	.medication-item,
	.preview-item,
	.medication-editor {
		padding: 0.9rem 1rem;
		border-radius: 18px;
		background: #f8fafc;
		display: grid;
		gap: 0.3rem;
	}

	.medication-item span,
	.medication-item small,
	.preview-item span,
	.preview-item small {
		color: #6b7280;
	}

	.lifestyle-block,
	.preview-block,
	.medications-panel {
		padding: 1rem;
		border-radius: 20px;
		background: #f8fafc;
	}

	.lifestyle-block ul,
	.preview-block ul {
		margin: 0.65rem 0 0;
		padding-left: 1rem;
	}

	.outline-btn,
	.primary-btn,
	.ghost-btn,
	.warning-btn,
	.close-btn,
	.text-btn {
		border-radius: 999px;
		font-weight: 700;
		cursor: pointer;
	}

	.outline-btn,
	.ghost-btn,
	.close-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	.primary-btn {
		border: 1px solid #0f766e;
		background: linear-gradient(135deg, #0f766e, #0ea5a4);
		color: #ffffff;
		padding: 0.78rem 1rem;
	}

	.warning-btn {
		border: 1px solid #f59e0b;
		background: linear-gradient(135deg, #f59e0b, #f97316);
		color: #ffffff;
		padding: 0.78rem 1rem;
	}

	.outline-btn,
	.ghost-btn {
		padding: 0.78rem 1rem;
	}

	.close-btn {
		width: 2.3rem;
		height: 2.3rem;
	}

	.text-btn {
		border: none;
		background: transparent;
		padding: 0;
		color: #0f766e;
	}

	.text-btn.danger {
		color: #b91c1c;
	}

	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(15, 23, 42, 0.45);
		backdrop-filter: blur(6px);
		display: grid;
		place-items: center;
		padding: 1rem;
		z-index: 60;
	}

	.modal-shell {
		width: min(1280px, 100%);
		max-height: calc(100vh - 2rem);
		overflow: auto;
	}

	.composer-grid {
		grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.9fr);
		margin-top: 1rem;
	}

	.composer-panel {
		padding: 1rem;
	}

	.form-grid label,
	.medication-editor label {
		display: grid;
		gap: 0.4rem;
	}

	.form-grid span,
	.medication-editor span {
		font-size: 0.84rem;
		font-weight: 700;
		color: #475569;
	}

	input,
	textarea {
		width: 100%;
		border: 1px solid #cbd5e1;
		border-radius: 16px;
		padding: 0.82rem 0.95rem;
		font: inherit;
		color: #111827;
		background: #ffffff;
		box-sizing: border-box;
	}

	textarea {
		resize: vertical;
	}

	.compact-head {
		align-items: center;
	}

	.form-error {
		margin: 0;
		padding: 0.85rem 1rem;
		border-radius: 16px;
		background: #fee2e2;
		color: #b91c1c;
		font-weight: 700;
	}

	.inline-error {
		margin-bottom: 0.25rem;
	}

	.composer-actions {
		justify-content: flex-end;
	}

	@media (max-width: 1100px) {
		.hero-card,
		.composer-grid {
			grid-template-columns: 1fr;
		}

		.detail-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.hero-grid,
		.detail-grid,
		.two-up,
		.preview-meta {
			grid-template-columns: 1fr;
		}

		.section-head,
		.prescription-head,
		.modal-header,
		.action-row {
			flex-direction: column;
		}

		.head-meta {
			justify-content: flex-start;
		}

		.composer-actions {
			align-items: stretch;
		}
	}
</style>
