<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let userData;
	let messages = [];
	let selectedPatient = null;
	let conversation = [];
	let newMessage = '';
	let newSubject = '';
	let loading = true;
	let unreadCount = 0;
	let sendingMessage = false;

	const unsubscribe = user.subscribe((value) => {
		userData = value;
	});

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadMessages();

		return unsubscribe;
	});

	async function loadMessages() {
		loading = true;
		try {
			const response = await api.get(`/api/doctor/${userData.id}/messages`);
			messages = response.data.messages || [];
			unreadCount = response.data.unread_count || 0;
		} catch (requestError) {
			console.error('Failed to load messages:', requestError);
		} finally {
			loading = false;
		}
	}

	async function loadConversation(patientId) {
		try {
			const response = await api.get(`/api/doctor/${userData.id}/messages/conversation/${patientId}`);
			conversation = response.data.messages || [];
			selectedPatient = {
				id: patientId,
				name: response.data.patient_name
			};

			const unreadMessages = conversation.filter(
				(message) => !message.is_read && message.recipient_id === userData.id
			);

			for (const message of unreadMessages) {
				await api.post(`/api/doctor/${userData.id}/messages/${message.id}/mark-read`);
			}

			await loadMessages();
		} catch (requestError) {
			console.error('Failed to load conversation:', requestError);
		}
	}

	async function sendMessage() {
		if (!newMessage.trim() || !selectedPatient) return;

		sendingMessage = true;
		try {
			await api.post(`/api/doctor/${userData.id}/messages/send`, {
				recipient_id: selectedPatient.id,
				recipient_type: 'patient',
				subject: newSubject || null,
				message: newMessage
			});

			newMessage = '';
			newSubject = '';
			await loadConversation(selectedPatient.id);
		} catch (requestError) {
			alert(requestError.response?.data?.detail || 'Failed to send message');
		} finally {
			sendingMessage = false;
		}
	}

	function formatDate(dateStr) {
		if (!dateStr) return '';

		const date = new Date(dateStr);
		const now = new Date();
		const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

		if (diffDays === 0) {
			return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		}

		if (diffDays === 1) {
			return 'Yesterday';
		}

		if (diffDays < 7) {
			return date.toLocaleDateString([], { weekday: 'short' });
		}

		return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
	}

	function getUniquePatients() {
		const patientMap = new Map();

		messages.forEach((message) => {
			let patientId;
			let patientName;

			if (message.sender_type === 'patient') {
				patientId = message.sender_id;
				patientName = message.sender_name;
			} else {
				patientId = message.recipient_id;
				patientName = message.recipient_name;
			}

			if (!patientMap.has(patientId)) {
				patientMap.set(patientId, {
					id: patientId,
					name: patientName,
					lastMessage: message.message,
					timestamp: message.created_at,
					hasUnread: message.sender_type === 'patient' && !message.is_read
				});
			}
		});

		return Array.from(patientMap.values());
	}
</script>

<DoctorWorkspaceShell
	title={uiText("Messages", $activeLocale)}
	subtitle={uiText("Patient conversations in a calmer clinical workspace, with the conversation list and thread separated clearly.", $activeLocale)}
	maxWidth="1360px"
>
	<svelte:fragment slot="actions">
		<div class="message-pill">Unread {unreadCount}</div>
	</svelte:fragment>

	<section class="messaging-shell">
		<aside class="conversation-list">
			<div class="panel-head">
				<p class="panel-kicker">{uiText("Inbox", $activeLocale)}</p>
				<h2>{uiText("Patient Conversations", $activeLocale)}</h2>
			</div>

			{#if loading}
				<p class="state-copy">{uiText("Loading messages...", $activeLocale)}</p>
			{:else if getUniquePatients().length === 0}
				<p class="state-copy">{uiText("No patient conversations yet.", $activeLocale)}</p>
			{:else}
				<div class="patient-list">
					{#each getUniquePatients() as patient}
						<button
							class:selected={selectedPatient?.id === patient.id}
							class:unread={patient.hasUnread}
							class="patient-item"
							on:click={() => loadConversation(patient.id)}
						>
							<div>
								<p class="patient-title">{patient.name}</p>
								<p class="patient-preview" data-localize-skip>{patient.lastMessage.slice(0, 72)}{patient.lastMessage.length > 72 ? '...' : ''}</p>
							</div>
							<div class="patient-meta">
								<span>{formatDate(patient.timestamp)}</span>
								{#if patient.hasUnread}
									<span class="unread-dot"></span>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</aside>

		<section class="conversation-panel">
			{#if !selectedPatient}
				<div class="empty-thread">
					<h2>{uiText("Select a patient", $activeLocale)}</h2>
					<p>{uiText("Open a conversation from the left panel to review history and send a message.", $activeLocale)}</p>
				</div>
			{:else}
				<div class="thread-head">
					<div>
						<p class="panel-kicker">{uiText("Active Thread", $activeLocale)}</p>
						<h2>{selectedPatient.name}</h2>
					</div>
					<button class="outline-btn" on:click={() => goto(`/doctor/patient/${selectedPatient.id}`)}>{uiText("Open Patient", $activeLocale)}</button>
				</div>

				<div class="message-stream">
					{#each conversation as message}
						<article class:sent={message.sender_type === 'doctor'} class="message-bubble">
							{#if message.subject}
								<p class="message-subject" data-localize-skip>{message.subject}</p>
							{/if}
							<p class="message-content" data-localize-skip>{message.message}</p>
							<p class="message-time">
								{new Date(message.created_at).toLocaleString()}
								{#if message.sender_type === 'doctor' && message.is_read}
									<span class="read-state">{uiText("Read", $activeLocale)}</span>
								{/if}
							</p>
						</article>
					{/each}
				</div>

				<div class="composer">
					<input class="subject-input" bind:value={newSubject} placeholder={uiText("Subject (optional)", $activeLocale)} />
					<textarea
						bind:value={newMessage}
						rows="4"
						placeholder={uiText("Write a message to the patient", $activeLocale)}
						on:keydown={(event) => {
							if (event.key === 'Enter' && !event.shiftKey) {
								event.preventDefault();
								sendMessage();
							}
						}}
					></textarea>
					<div class="composer-actions">
						<button class="primary-btn" disabled={!newMessage.trim() || sendingMessage} on:click={sendMessage}>
							{sendingMessage ? 'Sending...' : 'Send Message'}
						</button>
					</div>
				</div>
			{/if}
		</section>
	</section>
</DoctorWorkspaceShell>

<style>
	.message-pill,
	.conversation-list,
	.conversation-panel {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.message-pill {
		border-radius: 999px;
		padding: 0.8rem 1rem;
		font-weight: 700;
		color: #4f46e5;
	}

	.messaging-shell {
		display: grid;
		grid-template-columns: 330px minmax(0, 1fr);
		gap: 1rem;
		min-height: 720px;
	}

	.conversation-list,
	.conversation-panel {
		border-radius: 24px;
		padding: 1rem;
	}

	.panel-head,
	.thread-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.panel-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	h2,
	.patient-title,
	.message-subject {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.state-copy,
	.patient-preview,
	.message-time,
	.empty-thread p {
		color: #6b7280;
	}

	.patient-list,
	.message-stream {
		display: grid;
		gap: 0.75rem;
	}

	.patient-item {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 0.75rem;
		text-align: left;
		border: 1px solid #e2e8f0;
		background: #f8fafc;
		border-radius: 18px;
		padding: 0.95rem;
		cursor: pointer;
	}

	.patient-item.selected {
		border-color: #4f46e5;
		background: #eef2ff;
	}

	.patient-item.unread {
		background: #fffbeb;
	}

	.patient-title {
		font-weight: 800;
	}

	.patient-preview {
		margin: 0.3rem 0 0;
		line-height: 1.45;
	}

	.patient-meta {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.35rem;
		font-size: 0.85rem;
	}

	.unread-dot {
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 50%;
		background: #f59e0b;
	}

	.conversation-panel {
		display: grid;
		grid-template-rows: auto minmax(0, 1fr) auto;
		gap: 1rem;
	}

	.empty-thread {
		align-self: center;
		justify-self: center;
		text-align: center;
	}

	.message-stream {
		align-content: start;
		overflow: auto;
		padding-right: 0.2rem;
	}

	.message-bubble {
		max-width: 78%;
		padding: 0.95rem 1rem;
		border-radius: 20px;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
	}

	.message-bubble.sent {
		margin-left: auto;
		background: #eef2ff;
		border-color: #c7d2fe;
	}

	.message-content {
		margin: 0.35rem 0 0;
		color: #1f2937;
		line-height: 1.6;
	}

	.message-time {
		margin: 0.55rem 0 0;
		font-size: 0.82rem;
	}

	.read-state {
		margin-left: 0.45rem;
		font-weight: 700;
		color: #4f46e5;
	}

	.composer {
		display: grid;
		gap: 0.75rem;
	}

	.subject-input,
	textarea {
		width: 100%;
		border: 1px solid #d1d5db;
		border-radius: 18px;
		padding: 0.9rem 1rem;
		font: inherit;
		background: #f9fafb;
		color: #111827;
	}

	textarea {
		resize: vertical;
	}

	.composer-actions {
		display: flex;
		justify-content: flex-end;
	}

	.primary-btn,
	.outline-btn {
		border-radius: 999px;
		padding: 0.75rem 1rem;
		font-weight: 700;
		cursor: pointer;
	}

	.primary-btn {
		border: 1px solid #4f46e5;
		background: #4f46e5;
		color: #ffffff;
	}

	.outline-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	@media (max-width: 980px) {
		.messaging-shell {
			grid-template-columns: 1fr;
		}

		.message-bubble {
			max-width: 100%;
		}
	}
</style>
