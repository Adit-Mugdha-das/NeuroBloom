<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let patients = [];
	let pendingRequests = [];
	let analytics = null;
	let notifications = [];
	let unreadCount = 0;
	let loading = true;
	let error = '';
	let userData;
	let pollHandle = null;
	let toastTimer = null;
	let notificationToast = null;
	let latestNotificationFingerprint = null;
	let notificationsHydrated = false;

	const unsubscribe = user.subscribe((value) => {
		userData = value;
	});

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadData();
		pollHandle = window.setInterval(() => {
			loadNotifications();
		}, 45000);

		return () => {
			if (pollHandle) window.clearInterval(pollHandle);
			if (toastTimer) window.clearTimeout(toastTimer);
			unsubscribe();
		};
	});

	async function loadData() {
		loading = true;
		error = '';

		try {
			const [patientsResp, requestsResp, analyticsResp, notificationsResp] = await Promise.all([
				api.get(`/api/doctor/${userData.id}/patients`),
				api.get(`/api/doctor/${userData.id}/pending-requests`),
				api.get(`/api/doctor/${userData.id}/analytics`),
				api.get(`/api/doctor/${userData.id}/notifications`)
			]);

			patients = patientsResp.data.patients || [];
			pendingRequests = requestsResp.data.requests || [];
			analytics = analyticsResp.data;
			syncNotifications(notificationsResp.data.notifications || []);
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load doctor dashboard';
		} finally {
			loading = false;
		}
	}

	async function loadNotifications() {
		if (!userData) return;

		try {
			const response = await api.get(`/api/doctor/${userData.id}/notifications`);
			syncNotifications(response.data.notifications || []);
		} catch (requestError) {
			console.error('Error loading notifications:', requestError);
		}
	}

	function syncNotifications(nextNotifications) {
		const newestNotification = nextNotifications[0] ?? null;
		const nextFingerprint = newestNotification
			? `${newestNotification.id}:${newestNotification.created_at}`
			: null;

		if (notificationsHydrated && nextFingerprint && nextFingerprint !== latestNotificationFingerprint) {
			showNotificationToast(newestNotification);
		}

		notifications = nextNotifications;
		latestNotificationFingerprint = nextFingerprint;
		notificationsHydrated = true;
		updateUnreadCount();
	}

	function notificationSeenKey() {
		return userData ? `doctor-notifications-seen-${userData.id}` : 'doctor-notifications-seen';
	}

	function updateUnreadCount() {
		if (typeof localStorage === 'undefined') {
			unreadCount = 0;
			return;
		}

		const lastSeen = localStorage.getItem(notificationSeenKey());
		const lastSeenTime = lastSeen ? new Date(lastSeen).getTime() : 0;
		unreadCount = notifications.filter(
			(notification) => new Date(notification.created_at).getTime() > lastSeenTime
		).length;
	}

	function showNotificationToast(notification) {
		if (!notification) return;

		notificationToast = {
			title: notification.title,
			message: notification.message
		};

		if (toastTimer) window.clearTimeout(toastTimer);
		toastTimer = window.setTimeout(() => {
			notificationToast = null;
			toastTimer = null;
		}, 4200);
	}

	async function approveRequest(requestId) {
		if (!confirm('Approve this assignment request?')) return;

		try {
			await api.post(`/api/doctor/request/${requestId}/approve`, null, {
				params: {
					doctor_id: userData.id,
					treatment_goal: 'Improve cognitive function through targeted training'
				}
			});

			await loadData();
		} catch (requestError) {
			alert(requestError.response?.data?.detail || 'Failed to approve request');
		}
	}

	async function rejectRequest(requestId) {
		const reason = prompt('Reason for rejection (optional):');
		if (reason === null) return;

		try {
			await api.post(`/api/doctor/request/${requestId}/reject`, null, {
				params: {
					doctor_id: userData.id,
					notes: reason || 'Request declined'
				}
			});

			await loadData();
		} catch (requestError) {
			alert(requestError.response?.data?.detail || 'Failed to reject request');
		}
	}

	function viewPatient(patientId) {
		goto(`/doctor/patient/${patientId}`);
	}

	function formatDate(dateStr) {
		if (!dateStr) return 'No recent activity';

		return new Date(dateStr).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function lookupPatient(patientId) {
		return patients.find((patient) => patient.patient_id === patientId);
	}

	function getPatientDisplayName(patientSummary, patientDetails) {
		return patientDetails?.full_name || patientSummary?.name || patientSummary?.email || 'Patient';
	}

	$: attentionPatients = analytics?.high_risk_patients || [];
	$: snapshotCards = analytics
		? [
				{ label: 'Total Patients', value: analytics.overview.total_patients, tone: 'neutral' },
				{ label: 'Active Patients', value: analytics.overview.active_patients, tone: 'positive', meta: 'last 7 days' },
				{ label: 'Baseline Complete', value: analytics.overview.baseline_completed, tone: 'neutral' },
				{ label: 'Average Adherence', value: `${analytics.adherence.overall_adherence_rate}%`, tone: 'primary' }
			]
		: [];
	$: cohortMetrics = analytics
		? [
				{ label: 'Average Score', value: analytics.success_metrics.avg_session_score },
				{ label: 'Average Improvement', value: `${analytics.success_metrics.avg_improvement > 0 ? '+' : ''}${analytics.success_metrics.avg_improvement}` },
				{ label: 'Total Sessions', value: analytics.success_metrics.total_sessions_completed },
				{ label: 'Average Accuracy', value: `${analytics.success_metrics.avg_session_accuracy}%` }
			]
		: [];
</script>

<DoctorWorkspaceShell
	title={uiText("Dashboard", $activeLocale)}
	subtitle={uiText("A compact clinician overview focused on attention, pending actions, and a quick cohort readout.", $activeLocale)}
>
	{#if notificationToast}
		<div class="toast-shell" role="status" aria-live="polite">
			<div class="notification-toast">
				<p class="toast-label">{uiText("New notification", $activeLocale)}</p>
				<p class="toast-title">{notificationToast.title}</p>
				<p class="toast-message">{notificationToast.message}</p>
			</div>
		</div>
	{/if}

	{#if loading}
		<section class="state-card">
			<p>{uiText("Loading doctor dashboard...", $activeLocale)}</p>
		</section>
	{:else if error}
		<section class="state-card error-state">
			<p>{error}</p>
		</section>
	{:else}
<<<<<<< HEAD
=======
		<section class="panel-section">
			<LanguagePreferencePanel
				title={uiText("Language Preference", $activeLocale)}
				description="Set the clinician workspace language for dashboards, notifications, and task-facing copy."
				compact={true}
			/>
		</section>

>>>>>>> 3bf3510 (bangla interface refactoring)
		<section class="snapshot-grid">
			{#each snapshotCards as card}
				<article class="snapshot-card tone-{card.tone}">
					<p class="snapshot-label">{card.label}</p>
					<p class="snapshot-value">{card.value}</p>
					{#if card.meta}
						<p class="snapshot-meta">{card.meta}</p>
					{/if}
				</article>
			{/each}
		</section>

		<section class="panel-section">
			<div class="section-heading">
				<div>
					<p class="section-kicker warning">{uiText("Priority", $activeLocale)}</p>
					<h2>{uiText("Patients Requiring Attention", $activeLocale)}</h2>
				</div>
				<span class="section-count">{attentionPatients.length}</span>
			</div>

			{#if attentionPatients.length === 0}
				<div class="empty-card">
					<h3>{uiText("No urgent patient flags", $activeLocale)}</h3>
					<p>{uiText("Your monitored cohort has no current high-risk or medium-risk patients.", $activeLocale)}</p>
				</div>
			{:else}
				<div class="attention-grid">
					{#each attentionPatients as patient}
						{@const details = lookupPatient(patient.patient_id)}
						<article class="attention-card risk-{patient.risk_level}">
							<div class="attention-top">
								<div>
									<h3>{getPatientDisplayName(patient, details)}</h3>
									<p>{details?.diagnosis || patient.email}</p>
								</div>
								<span class="risk-badge {patient.risk_level}">{patient.risk_level}</span>
							</div>

							<div class="attention-stats">
								<div>
									<span>{uiText("Adherence", $activeLocale)}</span>
									<strong>{patient.adherence_rate}%</strong>
								</div>
								<div>
									<span>{uiText("Last Activity", $activeLocale)}</span>
									<strong>{formatDate(patient.last_activity)}</strong>
								</div>
							</div>

							<div class="risk-factors">
								<p>{uiText("Risk Factors", $activeLocale)}</p>
								<ul>
									{#each patient.risk_factors as factor}
										<li>{factor}</li>
									{/each}
								</ul>
							</div>

							<button class="primary-btn" on:click={() => viewPatient(patient.patient_id)}>
								{uiText("Open Patient", $activeLocale)}
							</button>
						</article>
					{/each}
				</div>
			{/if}
		</section>

		<section class="panel-section split-layout">
			<div class="request-panel">
				<div class="section-heading compact">
					<div>
						<p class="section-kicker">{uiText("Today", $activeLocale)}</p>
						<h2>{uiText("Assignment Requests", $activeLocale)}</h2>
					</div>
					<span class="section-count">{pendingRequests.length}</span>
				</div>

				{#if pendingRequests.length === 0}
					<div class="empty-card small">
						<p>{uiText("No pending requests right now.", $activeLocale)}</p>
					</div>
				{:else}
					<div class="request-list">
						{#each pendingRequests as request}
							<article class="request-card">
								<div class="request-copy">
									<h3>{request.patient_name || request.patient_email}</h3>
									<p>{request.diagnosis || 'Diagnosis not provided'}</p>
									{#if request.reason}
										<p class="request-reason">{request.reason}</p>
									{/if}
								</div>
								<div class="request-actions">
									<button class="outline-btn" on:click={() => rejectRequest(request.id)}>{uiText("Reject", $activeLocale)}</button>
									<button class="primary-btn" on:click={() => approveRequest(request.id)}>{uiText("Approve", $activeLocale)}</button>
								</div>
							</article>
						{/each}
					</div>
				{/if}
			</div>

			<div class="cohort-panel">
				<div class="section-heading compact">
					<div>
						<p class="section-kicker">{uiText("Overview", $activeLocale)}</p>
						<h2>{uiText("Cohort Snapshot", $activeLocale)}</h2>
					</div>
					<button class="outline-btn" on:click={() => goto('/doctor/analytics')}>{uiText("View Full Analytics", $activeLocale)}</button>
				</div>

				<div class="cohort-grid">
					{#each cohortMetrics as metric}
						<div class="cohort-card">
							<p>{metric.label}</p>
							<strong>{metric.value}</strong>
						</div>
					{/each}
				</div>
			</div>
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.primary-btn,
	.outline-btn {
		border-radius: 999px;
		padding: 0.8rem 1rem;
		font-weight: 700;
		cursor: pointer;
		transition: 180ms ease;
	}

	.outline-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	.primary-btn {
		border: 1px solid #4f46e5;
		background: #4f46e5;
		color: #ffffff;
		box-shadow: 0 12px 24px rgba(79, 70, 229, 0.18);
	}

	.outline-btn:hover {
		background: #eef2ff;
		border-color: #c7d2fe;
	}

	.primary-btn:hover {
		background: #4338ca;
	}

	.toast-shell {
		position: fixed;
		top: 1.25rem;
		right: 1.25rem;
		z-index: 10;
	}

	.notification-toast,
	.snapshot-card,
	.panel-section,
	.attention-card,
	.request-card,
	.cohort-card,
	.state-card,
	.empty-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.notification-toast {
		width: min(360px, calc(100vw - 2rem));
		border-radius: 16px;
		padding: 1rem 1.1rem;
		background: #ffffff;
		box-shadow: 0 8px 32px rgba(15, 23, 42, 0.14);
	}

	.toast-label {
		margin: 0;
		font-size: 0.74rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #4f46e5;
	}

	.toast-title {
		margin: 0.35rem 0 0;
		font-weight: 800;
		color: #111827;
	}

	.toast-message {
		margin: 0.35rem 0 0;
		color: #4b5563;
		line-height: 1.55;
	}

	.state-card,
	.empty-card,
	.panel-section {
		border-radius: 26px;
		padding: 1.35rem;
	}

	.error-state {
		border-color: rgba(239, 68, 68, 0.25);
		color: #b91c1c;
	}

	.snapshot-grid,
	.attention-grid,
	.cohort-grid {
		display: grid;
		gap: 1rem;
	}

	.snapshot-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.snapshot-card {
		border-radius: 22px;
		padding: 1.2rem 1.15rem;
	}

	.snapshot-label,
	.cohort-card p,
	.section-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #6b7280;
	}

	.section-kicker.warning {
		color: #d97706;
	}

	.snapshot-value {
		margin: 0.45rem 0 0;
		font-size: 2rem;
		font-weight: 800;
		line-height: 1;
		color: #111827;
	}

	.snapshot-meta {
		margin: 0.45rem 0 0;
		color: #6b7280;
	}

	.tone-primary {
		background: linear-gradient(160deg, #e0e7ff 0%, #f0f4ff 100%);
		border-color: #c7d2fe;
	}

	.tone-positive {
		background: linear-gradient(160deg, #d1fae5 0%, #f0fdf4 100%);
		border-color: #bbf7d0;
	}

	.section-heading {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.section-heading.compact {
		align-items: center;
	}

	h2,
	h3 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.section-count {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 2.4rem;
		height: 2.4rem;
		padding: 0 0.7rem;
		border-radius: 999px;
		background: #eef2ff;
		color: #4f46e5;
		font-weight: 800;
	}

	.attention-grid {
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
	}

	.attention-card {
		border-radius: 24px;
		padding: 1.15rem;
		border-left: 4px solid #f59e0b;
	}

	.attention-card.risk-high {
		border-left-color: #ef4444;
	}

	.attention-card.risk-medium {
		border-left-color: #f59e0b;
	}

	.attention-top,
	.attention-stats,
	.request-card,
	.split-layout {
		display: grid;
		gap: 1rem;
	}

	.attention-top {
		grid-template-columns: 1fr auto;
		align-items: start;
	}

	.attention-top p,
	.request-copy p,
	.empty-card p {
		margin: 0.35rem 0 0;
		color: #6b7280;
		line-height: 1.55;
	}

	.risk-badge {
		border-radius: 999px;
		padding: 0.35rem 0.7rem;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	.risk-badge.high {
		background: #fee2e2;
		color: #b91c1c;
	}

	.risk-badge.medium {
		background: #fef3c7;
		color: #b45309;
	}

	.risk-badge.low {
		background: #dcfce7;
		color: #15803d;
	}

	.attention-stats {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.attention-stats span,
	.risk-factors p {
		display: block;
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: #6b7280;
	}

	.attention-stats strong,
	.cohort-card strong {
		display: block;
		margin-top: 0.35rem;
		font-size: 1.1rem;
		color: #111827;
	}

	.risk-factors ul {
		margin: 0.55rem 0 0;
		padding-left: 1rem;
		color: #374151;
	}

	.split-layout {
		grid-template-columns: 1.15fr 0.85fr;
	}

	.request-list {
		display: grid;
		gap: 0.85rem;
	}

	.request-card {
		grid-template-columns: 1fr auto;
		align-items: center;
		border-radius: 20px;
		padding: 1rem;
	}

	.request-reason {
		color: #374151;
		font-weight: 600;
	}

	.request-actions {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.cohort-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.cohort-card {
		border-radius: 20px;
		padding: 1rem;
	}

	@media (max-width: 1024px) {
		.snapshot-grid,
		.split-layout {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.split-layout {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 760px) {
		.snapshot-grid,
		.cohort-grid,
		.attention-stats,
		.request-card {
			grid-template-columns: 1fr;
		}

		.section-heading,
		.attention-top,
		.request-actions {
			grid-template-columns: 1fr;
			display: grid;
		}

		.request-actions {
			justify-content: stretch;
		}
	}
</style>
