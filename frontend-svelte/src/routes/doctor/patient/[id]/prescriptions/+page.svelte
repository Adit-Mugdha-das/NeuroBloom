<script>
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
	subtitle="Structured digital prescribing with revision history, clinician review, PDF generation, and patient delivery."
	eyebrow="Doctor Patient Workspace"
	maxWidth="1360px"
>
	<svelte:fragment slot="actions">
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}`)}>Patient Overview</button>
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}/reports`)}>Reports</button>
		<button class="primary-btn" on:click={openCreateComposer}>Create Prescription</button>
	</svelte:fragment>

	{#if loading}
		<section class="state-card"><p>Loading prescriptions...</p></section>
	{:else if error}
		<section class="state-card error-state"><p>{error}</p></section>
	{:else}
		<section class="hero-card">
			<div>
				<p class="eyebrow-copy">Patient Prescription Record</p>
				<h2>{patientName}</h2>
				<p class="hero-copy">{patient?.diagnosis || patient?.treatment_goal || 'No diagnosis or treatment goal recorded yet.'}</p>
				{#if latestActivePrescription}
					<p class="hero-note">Current active prescription: {latestActivePrescription.title} · {latestActivePrescription.verification_id}</p>
				{/if}
			</div>
			<div class="hero-grid">
				{#each heroCards as card}
					<div class="hero-metric">
						<span>{card.label}</span>
						<strong>{card.value}</strong>
					</div>
				{/each}
			</div>
		</section>

		<section class="panel-card section-card">
			<div class="section-head">
				<div>
					<p class="section-kicker">Prescription History</p>
					<h3>Issued documents and revisions</h3>
				</div>
				<span class="meta-pill">{prescriptions.length} record{prescriptions.length === 1 ? '' : 's'}</span>
			</div>

			{#if prescriptions.length === 0}
				<div class="empty-state">
					<h3>No prescriptions have been issued yet</h3>
					<p>Create the first structured prescription to add it to the patient’s history and deliver it through the patient portal.</p>
					<button class="primary-btn" on:click={openCreateComposer}>Create First Prescription</button>
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
									<h3>{prescription.title}</h3>
									<p class="summary-copy">{prescription.summary || prescription.patient_instructions}</p>
								</div>
								<div class="head-meta">
									<span>Issued {formatDateTime(prescription.created_at)}</span>
									<span>Version {prescription.version_number}</span>
								</div>
							</div>

							<div class="detail-grid">
								<div>
									<span>Patient instructions</span>
									<strong>{prescription.patient_instructions}</strong>
								</div>
								<div>
									<span>Review date</span>
									<strong>{formatDate(prescription.review_date)}</strong>
								</div>
								<div>
									<span>Valid until</span>
									<strong>{formatDate(prescription.valid_until)}</strong>
								</div>
								<div>
									<span>Medication count</span>
									<strong>{prescription.medication_count}</strong>
								</div>
							</div>

							{#if prescription.retired_reason || prescription.retired_at}
								<div class="status-note-card">
									<p class="card-kicker">Status Update</p>
									<p>
										{#if prescription.retired_reason}
											{prescription.retired_reason}
										{:else}
											This prescription is no longer active.
										{/if}
									</p>
									{#if prescription.retired_at}
										<small>Updated {formatDateTime(prescription.retired_at)}</small>
									{/if}
								</div>
							{/if}

							{#if prescription.medications?.length}
								<div class="medication-list">
									{#each prescription.medications as medication}
										<div class="medication-item">
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
									<p class="card-kicker">Lifestyle Recommendations</p>
									<ul>
										{#each prescription.lifestyle_plan as item}
											<li>{item}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<div class="action-row">
								<button class="ghost-btn" on:click={() => openPdf(prescription)}>View PDF</button>
								<button class="ghost-btn" on:click={() => downloadPdf(prescription)}>Download</button>
								<button class="primary-btn" on:click={() => openRevisionComposer(prescription)}>Edit And Reissue</button>
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
		aria-label="Close prescription composer"
		on:click={closeComposer}
		on:keydown={handleOverlayKeydown}
	>
		<div
			class="modal-shell"
			role="dialog"
			aria-modal="true"
			aria-label="Prescription composer"
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
							<span>Prescription title</span>
							<input bind:value={draft.title} placeholder="Cognitive support medication plan" />
						</label>

						<label>
							<span>Clinical summary</span>
							<textarea bind:value={draft.summary} rows="3" placeholder="Short diagnostic and prescribing summary."></textarea>
						</label>

						<label>
							<span>Patient instructions</span>
							<textarea bind:value={draft.patient_instructions} rows="4" placeholder="Explain how the patient should follow this plan."></textarea>
						</label>

						<div class="two-up">
							<label>
								<span>Valid until</span>
								<input type="date" bind:value={draft.valid_until} />
							</label>
							<label>
								<span>Review date</span>
								<input type="date" bind:value={draft.review_date} />
							</label>
						</div>

						<label>
							<span>Follow-up plan</span>
							<textarea bind:value={draft.follow_up_plan} rows="2" placeholder="Follow-up review, monitoring, or lab instructions."></textarea>
						</label>

						<label>
							<span>Clinician notes</span>
							<textarea bind:value={draft.clinician_notes} rows="3" placeholder="Private clinical notes to keep in the record."></textarea>
						</label>

						<label>
							<span>Lifestyle recommendations</span>
							<textarea bind:value={draft.lifestyle_plan_text} rows="4" placeholder="One recommendation per line."></textarea>
						</label>
					</div>

					<div class="medications-panel">
						<div class="section-head compact-head">
							<div>
								<p class="section-kicker">Medication Items</p>
								<h3>Dosage, schedule, and duration</h3>
							</div>
							<button class="ghost-btn" on:click={addMedication}>Add Item</button>
						</div>

						<div class="medication-editor-list">
							{#each draft.medications as medication, index}
								<div class="medication-editor">
									<div class="two-up">
										<label>
											<span>Medication name</span>
											<input value={medication.name} on:input={(event) => updateMedication(index, 'name', event.currentTarget.value)} placeholder="Donepezil" />
										</label>
										<label>
											<span>Dosage</span>
											<input value={medication.dosage} on:input={(event) => updateMedication(index, 'dosage', event.currentTarget.value)} placeholder="5 mg" />
										</label>
									</div>
									<div class="two-up">
										<label>
											<span>Frequency</span>
											<input value={medication.frequency} on:input={(event) => updateMedication(index, 'frequency', event.currentTarget.value)} placeholder="Once daily" />
										</label>
										<label>
											<span>Duration</span>
											<input value={medication.duration} on:input={(event) => updateMedication(index, 'duration', event.currentTarget.value)} placeholder="30 days" />
										</label>
									</div>
									<label>
										<span>Instructions</span>
										<input value={medication.instructions} on:input={(event) => updateMedication(index, 'instructions', event.currentTarget.value)} placeholder="Take after dinner" />
									</label>
									{#if draft.medications.length > 1}
										<button class="text-btn danger" on:click={() => removeMedication(index)}>Remove item</button>
									{/if}
								</div>
							{/each}
						</div>
					</div>

					{#if formError}
						<p class="form-error">{formError}</p>
					{/if}

					<div class="action-row composer-actions">
						<button class="ghost-btn" on:click={closeComposer}>Cancel</button>
						<button class="primary-btn" disabled={saving} on:click={savePrescription}>
							{saving ? 'Saving...' : editingPrescription ? 'Issue Revision' : 'Issue Prescription'}
						</button>
					</div>
				</section>

				<aside class="composer-panel preview-panel">
					<p class="section-kicker">Live Review</p>
					<h3>{draft.title || 'Prescription title preview'}</h3>
					<p class="preview-summary">{draft.summary || draft.patient_instructions || 'A short summary and patient-facing instructions will appear here as you compose the prescription.'}</p>

					<div class="preview-meta">
						<div><span>Patient</span><strong>{patientName}</strong></div>
						<div><span>Diagnosis</span><strong>{patient?.diagnosis || 'Not recorded'}</strong></div>
						<div><span>Review date</span><strong>{draft.review_date || 'Not scheduled'}</strong></div>
						<div><span>Status</span><strong>{draft.status}</strong></div>
					</div>

					<div class="preview-block">
						<p class="card-kicker">Medications</p>
						{#if previewMedications.length}
							{#each previewMedications as medication}
								<div class="preview-item">
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
							<p class="empty-copy">Medication items will appear here.</p>
						{/if}
					</div>

					<div class="preview-block">
						<p class="card-kicker">Lifestyle Recommendations</p>
						{#if previewLifestyleItems.length}
							<ul>
								{#each previewLifestyleItems as item}
									<li>{item}</li>
								{/each}
							</ul>
						{:else}
							<p class="empty-copy">Lifestyle guidance will appear here.</p>
						{/if}
					</div>

					<div class="preview-block">
						<p class="card-kicker">Patient Instructions</p>
						<p>{draft.patient_instructions || 'Patient-facing instructions will appear here.'}</p>
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
		background: #ffffff;
		border: 1px solid #e5e7eb;
		border-radius: 24px;
		box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
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
		background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
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