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

<div class="messages-shell" data-localize-skip>
	<header class="messages-topbar glass-card">
		<div class="topbar-left">
			<button class="back-btn" on:click={() => goto('/dashboard')} title={t('Back to Dashboard')}>
				<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
			</button>
			<div>
				<p class="eyebrow">NeuroBloom</p>
				<h1>{t('Messages')}</h1>
			</div>
		</div>
		{#if doctorInfo}
			<div class="doctor-pill">
				<div class="doctor-avatar-sm">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
				</div>
				<div>
					<p class="pill-name">{doctorInfo.name}</p>
					<p class="pill-role">
						<span class="online-dot"></span>
						{t('Healthcare Provider')}
					</p>
				</div>
			</div>
		{/if}
	</header>

	<div class="chat-area glass-card">
		{#if loading}
			<div class="state-panel">
				<div class="spinner"></div>
				<p>{t('Loading messages...')}</p>
			</div>
		{:else if !doctorInfo}
			<div class="state-panel">
				<div class="state-icon">
					<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
				</div>
				<h2>{t('No Doctor Assigned')}</h2>
				<p>{t('Connect with a healthcare provider to start secure messaging')}</p>
				<button class="primary-btn" on:click={() => goto('/find-doctor')}>{t('Find a Doctor')}</button>
			</div>
		{:else if conversation.length === 0}
			<div class="state-panel">
				<div class="state-icon">
					<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2m0 0H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h18a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2z"/></svg>
				</div>
				<h2>{t('Start Your Conversation')}</h2>
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
							<div class="msg-avatar">
								<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
							</div>
						{/if}
						<div class="bubble">
							{#if message.subject}
								<p class="bubble-subject">{message.subject}</p>
							{/if}
							<p class="bubble-text">{message.message}</p>
							<div class="bubble-meta">
								<span>{formatConversationTime(message.created_at)}</span>
								{#if message.sender_type === 'patient'}
									<span class="read-mark" class:seen={message.is_read}>
										{#if message.is_read}
											<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
										{:else}
											<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
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

	{#if doctorInfo}
		<div class="composer glass-card">
			<input
				type="text"
				class="composer-subject"
				placeholder={t('Subject (optional)')}
				bind:value={newSubject}
			/>
			<textarea
				class="composer-body"
				placeholder={t('Type your message...')}
				bind:value={newMessage}
				rows="3"
				on:keydown={(e) => {
					if (e.key === 'Enter' && !e.shiftKey) {
						e.preventDefault();
						sendMessage();
					}
				}}
			></textarea>
			<div class="composer-footer">
				<p class="hint">{t('Press Enter to send')} • {t('Shift+Enter for new line')}</p>
				<button
					class="send-btn"
					on:click={sendMessage}
					disabled={!newMessage.trim() || sendingMessage}
				>
					{sendingMessage ? t('Sending...') : t('Send Message')}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	
	
	:global(body) {
		background:
			radial-gradient(circle at 10% 20%, rgba(79, 70, 229, 0.08), transparent 30%),
			radial-gradient(circle at 90% 10%, rgba(56, 189, 248, 0.1), transparent 32%),
			linear-gradient(135deg, #f0f7ff, #e6f0ff);
	}

	.messages-shell {
		min-height: 100vh;
		width: 100%;
		max-width: 1100px;
		margin: 0 auto;
		padding: 1.5rem;
		background:
			radial-gradient(circle at top left, rgba(79, 70, 229, 0.1), transparent 28%),
			radial-gradient(circle at right top, rgba(34, 211, 238, 0.14), transparent 26%),
			linear-gradient(135deg, rgba(239, 246, 255, 0.92), rgba(224, 242, 254, 0.9));
		display: grid;
		grid-template-rows: auto 1fr auto;
		gap: 0.9rem;
		box-sizing: border-box;
	}

	.glass-card {
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: blur(14px);
		border: 1px solid rgba(255, 255, 255, 0.6);
		border-radius: 24px;
		box-shadow:
			0 12px 40px rgba(15, 23, 42, 0.08),
			inset 0 1px 0 rgba(255, 255, 255, 0.5);
		box-sizing: border-box;
	}

	.messages-topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.25rem;
	}

	.topbar-left {
		display: flex;
		align-items: center;
		gap: 0.9rem;
	}

	.back-btn {
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 1px solid #dbeafe;
		background: rgba(239, 246, 255, 0.9);
		color: #334155;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		flex-shrink: 0;
		transition: all 0.15s ease;
	}

	.back-btn:hover {
		background: #dbeafe;
		transform: translateX(-1px);
	}

	.eyebrow {
		margin: 0;
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 0.09em;
		font-weight: 800;
		color: #4f46e5;
	}

	.messages-topbar h1 {
		margin: 0.1rem 0 0;
		font-size: 1.45rem;
		color: #111827;
		font-weight: 800;
	}

	.doctor-pill {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		background: rgba(79, 70, 229, 0.08);
		border: 1px solid rgba(99, 102, 241, 0.2);
		border-radius: 999px;
		padding: 0.45rem 0.9rem 0.45rem 0.45rem;
	}

	.doctor-avatar-sm {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
	}

	.pill-name {
		margin: 0;
		font-size: 0.88rem;
		font-weight: 800;
		color: #111827;
	}

	.pill-role {
		margin: 0.1rem 0 0;
		font-size: 0.75rem;
		color: #64748b;
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.online-dot {
		width: 7px;
		height: 7px;
		background: #10b981;
		border-radius: 50%;
		animation: pulse 2s infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.45; }
	}

	.chat-area {
		overflow: hidden;
		display: flex;
		flex-direction: column;
		min-height: 440px;
		border-radius: 24px;
	}

	.state-panel {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.85rem;
		padding: 3rem 2rem;
		text-align: center;
		flex: 1;
	}

	.state-icon {
		width: 72px;
		height: 72px;
		border-radius: 50%;
		background: rgba(79, 70, 229, 0.08);
		display: flex;
		align-items: center;
		justify-content: center;
		color: #4f46e5;
	}

	.state-panel h2 {
		margin: 0;
		font-size: 1.25rem;
		color: #111827;
	}

	.state-panel p {
		margin: 0;
		color: #64748b;
		font-size: 0.9rem;
		max-width: 340px;
		line-height: 1.55;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid #e2e8f0;
		border-top-color: #4f46e5;
		border-radius: 50%;
		animation: spin 0.9s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.primary-btn {
		margin-top: 0.5rem;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: white;
		border: none;
		padding: 0.75rem 1.6rem;
		border-radius: 999px;
		font-weight: 700;
		cursor: pointer;
		font-size: 0.9rem;
		transition: opacity 0.2s;
	}

	.primary-btn:hover {
		opacity: 0.88;
	}

	.messages-scroll {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem 2rem;
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
	}

	.messages-scroll::-webkit-scrollbar {
		width: 5px;
	}

	.messages-scroll::-webkit-scrollbar-track {
		background: transparent;
	}

	.messages-scroll::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 3px;
	}

	.date-divider {
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0.75rem 0;
	}

	.date-divider span {
		background: rgba(99, 102, 241, 0.12);
		color: #4f46e5;
		padding: 0.35rem 0.95rem;
		border-radius: 999px;
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.04em;
	}

	.message-row {
		display: flex;
		gap: 0.55rem;
		align-items: flex-end;
	}

	.message-row.sent {
		flex-direction: row-reverse;
	}

	.msg-avatar {
		width: 30px;
		height: 30px;
		border-radius: 50%;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		flex-shrink: 0;
	}

	.bubble {
		max-width: 70%;
		padding: 0.8rem 1rem;
		border-radius: 18px;
		word-break: break-word;
	}

	.message-row.sent .bubble {
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: white;
		border-bottom-right-radius: 4px;
		box-shadow: 0 10px 24px rgba(79, 70, 229, 0.22);
	}

	.message-row.received .bubble {
		background: #ffffff;
		border: 1px solid #bfdbfe;
		box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
		color: #111827;
		border-bottom-left-radius: 4px;
	}

	.bubble-subject {
		margin: 0 0 0.45rem;
		font-weight: 800;
		font-size: 0.88rem;
		padding-bottom: 0.45rem;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}

	.message-row.sent .bubble-subject {
		border-bottom-color: rgba(255, 255, 255, 0.28);
	}

	.bubble-text {
		margin: 0;
		line-height: 1.5;
		font-size: 0.92rem;
		white-space: pre-wrap;
	}

	.bubble-meta {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-top: 0.45rem;
		font-size: 0.72rem;
		opacity: 0.65;
	}

	.message-row.sent .bubble-meta {
		justify-content: flex-end;
	}

	.read-mark {
		display: flex;
		align-items: center;
	}

	.read-mark.seen {
		opacity: 1;
		color: #6ee7b7;
	}

	.composer {
		padding: 1rem 1.25rem;
		display: grid;
		gap: 0.65rem;
	}

	.composer-subject,
	.composer-body {
		width: 100%;
		border: 1px solid #dbeafe;
		border-radius: 14px;
		padding: 0.8rem 1rem;
		font: inherit;
		font-size: 0.92rem;
		background: rgba(248, 250, 252, 0.92);
		color: #111827;
		box-sizing: border-box;
		outline: none;
		transition: border-color 0.15s, box-shadow 0.15s;
	}

	.composer-subject:focus,
	.composer-body:focus {
		border-color: rgba(99, 102, 241, 0.55);
		box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.08);
	}

	.composer-body {
		resize: vertical;
		min-height: 90px;
	}

	.composer-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.hint {
		margin: 0;
		font-size: 0.73rem;
		color: #94a3b8;
	}

	.send-btn {
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		border: none;
		color: white;
		padding: 0.75rem 1.4rem;
		border-radius: 999px;
		font-weight: 700;
		font-size: 0.88rem;
		cursor: pointer;
		flex-shrink: 0;
		transition: opacity 0.2s, transform 0.15s;
		box-shadow: 0 10px 22px rgba(79, 70, 229, 0.22);
	}

	.send-btn:hover:not(:disabled) {
		opacity: 0.88;
		transform: translateY(-1px);
	}

	.send-btn:disabled {
		opacity: 0.38;
		cursor: not-allowed;
		box-shadow: none;
	}

	@media (max-width: 640px) {
		.messages-shell {
			padding: 0.75rem;
		}

		.doctor-pill {
			display: none;
		}

		.bubble {
			max-width: 82%;
		}

		.messages-scroll {
			padding: 1rem;
		}

		.composer-footer {
			flex-direction: column;
			align-items: stretch;
		}

		.send-btn {
			width: 100%;
		}
	}

</style>
