<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { locale, translateText } from '$lib/i18n';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let userData;
	let doctorInfo = null;
	let conversation = [];
	let newMessage = '';
	let newSubject = '';
	let loading = true;
	let sendingMessage = false;

	const unsubscribe = user.subscribe((value) => {
		userData = value;
	});

	function t(text) {
		return translateText(text, $locale);
	}

	function localeCode() {
		return $locale === 'bn' ? 'bn-BD' : 'en-US';
	}

	onMount(() => {
		if (!userData) {
			goto('/login');
			return;
		}

		loadConversation();
		const interval = setInterval(loadConversation, 30000);

		return () => {
			unsubscribe();
			clearInterval(interval);
		};
	});

	async function loadConversation() {
		loading = true;

		try {
			const response = await api.get(`/api/doctor/patient/${userData.id}/messages/with-doctor`);

			if (!response.data.has_doctor) {
				doctorInfo = null;
				conversation = [];
				return;
			}

			doctorInfo = {
				id: response.data.doctor_id,
				name: response.data.doctor_name
			};
			conversation = response.data.messages || [];

			const unreadMessages = conversation.filter(
				(message) => !message.is_read && message.recipient_id === userData.id
			);

			if (unreadMessages.length > 0) {
				await Promise.all(
					unreadMessages.map((message) =>
						api.post(`/api/auth/patient/${userData.id}/messages/${message.id}/mark-read`)
					)
				);
			}
		} catch (error) {
			console.error('Failed to load conversation:', error);
			doctorInfo = null;
			conversation = [];
		} finally {
			loading = false;
		}
	}

	async function sendMessage() {
		if (!newMessage.trim() || !doctorInfo || sendingMessage) return;

		sendingMessage = true;
		try {
			await api.post(`/api/auth/patient/${userData.id}/messages/send`, {
				recipient_id: doctorInfo.id,
				recipient_type: 'doctor',
				subject: newSubject.trim() || null,
				message: newMessage.trim()
			});

			newMessage = '';
			newSubject = '';
			await loadConversation();
		} catch (error) {
			alert(
				`${t('Failed to send message')}: ${t(error.response?.data?.detail || 'Unknown error')}`
			);
		} finally {
			sendingMessage = false;
		}
	}

	function formatConversationDate(dateStr) {
		if (!dateStr) return '';

		return new Date(dateStr).toLocaleDateString(localeCode(), {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function formatConversationTime(dateStr) {
		if (!dateStr) return '';

		return new Date(dateStr).toLocaleTimeString(localeCode(), {
			hour: 'numeric',
			minute: '2-digit'
		});
	}
</script>

<div class="messages-page" data-localize-skip>
	<div class="chat-container">
		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<p>{t('Loading messages...')}</p>
			</div>
		{:else if !doctorInfo}
			<div class="no-doctor-card">
				<div class="icon-container">
					<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2M8 21h16M8 21v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5"/><circle cx="20" cy="8" r="4"/></svg>
				</div>
				<h2>{t('No Doctor Assigned')}</h2>
				<p>{t('Connect with a healthcare provider to start secure messaging')}</p>
				<button on:click={() => goto('/find-doctor')} class="find-doctor-btn">
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
					{t('Find a Doctor')}
				</button>
				<button on:click={() => goto('/dashboard')} class="back-link">{t('Back to Dashboard')}</button>
			</div>
		{:else}
			<div class="chat-header">
				<button
					on:click={() => goto('/dashboard')}
					class="back-button"
					title={t('Back to Dashboard')}
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
				</button>
				<div class="doctor-avatar">
					<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
				</div>
				<div class="doctor-details">
					<h2>{doctorInfo.name}</h2>
					<p class="status-text">
						<span class="status-indicator"></span>
						{t('Healthcare Provider')}
					</p>
				</div>
			</div>

			<div class="messages-area">
				{#if conversation.length === 0}
					<div class="empty-state">
						<div class="empty-icon">💬</div>
						<h3>{t('Start Your Conversation')}</h3>
						<p>{t('Send a message to connect with your healthcare provider')}</p>
					</div>
				{:else}
					<div class="messages-scroll">
						{#each conversation as message, index}
							{@const showDate =
								index === 0 ||
								new Date(conversation[index - 1].created_at).toDateString() !==
									new Date(message.created_at).toDateString()}

							{#if showDate}
								<div class="date-divider">
									<span>{formatConversationDate(message.created_at)}</span>
								</div>
							{/if}

							<div class="message-row {message.sender_type === 'patient' ? 'sent' : 'received'}">
								{#if message.sender_type === 'doctor'}
									<div class="message-avatar">
										<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
									</div>
								{/if}

								<div class="message-bubble">
									{#if message.subject}
										<div class="message-subject">{message.subject}</div>
									{/if}
									<div class="message-text">{message.message}</div>
									<div class="message-meta">
										<span class="message-time">{formatConversationTime(message.created_at)}</span>
										{#if message.sender_type === 'patient'}
											<span class="read-indicator" class:read={message.is_read}>
												{#if message.is_read}
													<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
												{:else}
													<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
												{/if}
											</span>
										{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<div class="message-input-container">
				<div class="composer">
					<input
						type="text"
						class="subject-input"
						placeholder={t('Subject (optional)')}
						bind:value={newSubject}
					/>
					<textarea
						placeholder={t('Type your message...')}
						bind:value={newMessage}
						rows="3"
						on:keydown={(event) => {
							if (event.key === 'Enter' && !event.shiftKey) {
								event.preventDefault();
								sendMessage();
							}
						}}
						class="message-textarea"
					></textarea>
					<div class="composer-actions">
						<div class="input-hint">{t('Press Enter to send')} • {t('Shift+Enter for new line')}</div>
						<button
							class="send-button"
							on:click={sendMessage}
							disabled={!newMessage.trim() || sendingMessage}
							title={t('Send message (Enter)')}
						>
							{sendingMessage ? t('Sending...') : t('Send Message')}
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.messages-page {
		width: 100%;
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 1rem;
	}

	.chat-container {
		width: 100%;
		max-width: 900px;
		height: calc(100vh - 2rem);
		max-height: 800px;
		background: #ffffff;
		border-radius: 16px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 1.5rem;
	}

	.spinner {
		width: 48px;
		height: 48px;
		border: 4px solid #e0e0e0;
		border-top-color: #667eea;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-state p {
		color: #666;
		font-size: 1.1rem;
	}

	.no-doctor-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		padding: 3rem;
		text-align: center;
	}

	.icon-container {
		width: 100px;
		height: 100px;
		background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 2rem;
		color: #667eea;
	}

	.no-doctor-card h2 {
		font-size: 1.75rem;
		color: #333;
		margin-bottom: 0.75rem;
	}

	.no-doctor-card p {
		color: #666;
		font-size: 1.05rem;
		margin-bottom: 2rem;
		max-width: 400px;
	}

	.find-doctor-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
	}

	.find-doctor-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
	}

	.back-link {
		margin-top: 1.5rem;
		background: none;
		border: none;
		color: #667eea;
		font-size: 0.95rem;
		cursor: pointer;
		padding: 0.5rem 1rem;
		transition: opacity 0.2s;
	}

	.back-link:hover {
		opacity: 0.7;
	}

	.chat-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1.25rem 1.5rem;
		background: #ffffff;
		border-bottom: 1px solid #e5e7eb;
		flex-shrink: 0;
	}

	.back-button {
		background: #f3f4f6;
		border: none;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.2s ease;
		color: #374151;
	}

	.back-button:hover {
		background: #e5e7eb;
		transform: scale(1.05);
	}

	.doctor-avatar {
		width: 48px;
		height: 48px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
	}

	.doctor-details {
		flex: 1;
	}

	.doctor-details h2 {
		font-size: 1.125rem;
		font-weight: 600;
		color: #111827;
		margin: 0 0 0.25rem 0;
	}

	.status-text {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #6b7280;
		margin: 0;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		background: #10b981;
		border-radius: 50%;
		display: inline-block;
		animation: pulse 2s infinite;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	.messages-area {
		flex: 1;
		overflow: hidden;
		background: #f9fafb;
	}

	.messages-scroll {
		height: 100%;
		overflow-y: auto;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.messages-scroll::-webkit-scrollbar {
		width: 6px;
	}

	.messages-scroll::-webkit-scrollbar-track {
		background: transparent;
	}

	.messages-scroll::-webkit-scrollbar-thumb {
		background: #d1d5db;
		border-radius: 3px;
	}

	.messages-scroll::-webkit-scrollbar-thumb:hover {
		background: #9ca3af;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 1rem;
		padding: 2rem;
		text-align: center;
	}

	.empty-icon {
		font-size: 4rem;
		opacity: 0.3;
	}

	.empty-state h3 {
		font-size: 1.25rem;
		color: #374151;
		margin: 0;
	}

	.empty-state p {
		color: #6b7280;
		font-size: 0.95rem;
		margin: 0;
		max-width: 300px;
	}

	.date-divider {
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 1rem 0;
	}

	.date-divider span {
		background: #e5e7eb;
		color: #6b7280;
		padding: 0.375rem 1rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.message-row {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
		margin-bottom: 0.25rem;
	}

	.message-row.sent {
		flex-direction: row-reverse;
	}

	.message-avatar {
		width: 32px;
		height: 32px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
	}

	.message-bubble {
		max-width: 65%;
		padding: 0.75rem 1rem;
		border-radius: 16px;
		position: relative;
		word-wrap: break-word;
		animation: fadeIn 0.2s ease;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.message-row.sent .message-bubble {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-bottom-right-radius: 4px;
	}

	.message-row.received .message-bubble {
		background: #ffffff;
		color: #111827;
		border: 1px solid #e5e7eb;
		border-bottom-left-radius: 4px;
	}

	.message-subject {
		font-weight: 600;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}

	.message-row.sent .message-subject {
		border-bottom-color: rgba(255, 255, 255, 0.3);
	}

	.message-text {
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-word;
		font-size: 0.95rem;
	}

	.message-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
	}

	.message-row.sent .message-meta {
		justify-content: flex-end;
	}

	.message-time {
		opacity: 0.7;
	}

	.read-indicator {
		display: flex;
		align-items: center;
		opacity: 0.7;
	}

	.read-indicator.read {
		color: #10b981;
		opacity: 1;
	}

	.message-input-container {
		background: #ffffff;
		border-top: 1px solid #e5e7eb;
		padding: 1rem 1.5rem;
		flex-shrink: 0;
	}

	.composer {
		display: grid;
		gap: 0.75rem;
	}

	.subject-input,
	.message-textarea {
		width: 100%;
		border: 1px solid #d1d5db;
		border-radius: 18px;
		padding: 0.9rem 1rem;
		font: inherit;
		background: #f9fafb;
		color: #111827;
	}

	.message-textarea {
		resize: vertical;
		min-height: 96px;
	}

	.composer-actions {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.input-hint {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	.send-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border: none;
		color: white;
		cursor: pointer;
		padding: 0.85rem 1.4rem;
		border-radius: 999px;
		font-weight: 700;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.send-button:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}

	.send-button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	@media (max-width: 768px) {
		.messages-page {
			padding: 0;
		}

		.chat-container {
			height: 100vh;
			max-height: 100vh;
			border-radius: 0;
		}

		.message-bubble {
			max-width: 80%;
		}

		.doctor-details h2 {
			font-size: 1rem;
		}

		.chat-header,
		.message-input-container {
			padding: 1rem;
		}

		.composer-actions {
			flex-direction: column;
			align-items: stretch;
		}

		.send-button {
			width: 100%;
		}
	}
</style>
