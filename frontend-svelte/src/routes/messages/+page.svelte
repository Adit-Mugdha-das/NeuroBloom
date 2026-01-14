<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let userData;
	let doctorInfo = null;
	let conversation = [];
	let newMessage = '';
	let newSubject = '';
	let loading = true;
	let sendingMessage = false;
	let unreadCount = 0;
	
	const unsubscribe = user.subscribe(value => {
		userData = value;
	});
	
	onMount(() => {
		if (!userData) {
			goto('/login');
			return;
		}
		
		loadConversation();
		
		// Poll for new messages every 30 seconds
		const interval = setInterval(loadConversation, 30000);
		
		return () => {
			unsubscribe();
			clearInterval(interval);
		};
	});
	
	async function loadConversation() {
		try {
			console.log('Loading conversation for patient:', userData.id);
			
			// Load the conversation (includes doctor check)
			const response = await api.get(`/api/doctor/patient/${userData.id}/messages/with-doctor`);
			console.log('Conversation response:', response.data);
			
			if (response.data.has_doctor) {
				doctorInfo = {
					id: response.data.doctor_id,
					name: response.data.doctor_name
				};
				conversation = response.data.messages;
				
				// Mark unread messages as read
				const unreadMessages = conversation.filter(m => 
					!m.is_read && m.recipient_id === userData.id
				);
				
				unreadCount = unreadMessages.length;
				
				for (const msg of unreadMessages) {
					await api.post(`/api/auth/patient/${userData.id}/messages/${msg.id}/mark-read`);
				}
			} else {
				console.log('No doctor assigned according to conversation API');
				doctorInfo = null;
			}
			
			loading = false;
		} catch (err) {
			console.error('Failed to load conversation:', err);
			console.error('Error details:', err.response?.data);
			doctorInfo = null;
			loading = false;
		}
	}
	
	async function sendMessage() {
		if (!newMessage.trim() || !doctorInfo) return;
		
		sendingMessage = true;
		try {
			await api.post(`/api/auth/patient/${userData.id}/messages/send`, {
				recipient_id: doctorInfo.id,
				recipient_type: 'doctor',
				subject: newSubject || null,
				message: newMessage
			});
			
			newMessage = '';
			newSubject = '';
			await loadConversation();
		} catch (err) {
			alert('Failed to send message: ' + (err.response?.data?.detail || 'Unknown error'));
		} finally {
			sendingMessage = false;
		}
	}
	
	function formatDate(dateStr) {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleString();
	}
</script>

<div class="messages-page">
	<div class="chat-container">
		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<p>Loading messages...</p>
			</div>
		{:else if !doctorInfo}
			<div class="no-doctor-card">
				<div class="icon-container">
					<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2M8 21h16M8 21v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5"/><circle cx="20" cy="8" r="4"/></svg>
				</div>
				<h2>No Doctor Assigned</h2>
				<p>Connect with a healthcare provider to start secure messaging</p>
				<button on:click={() => goto('/find-doctor')} class="find-doctor-btn">
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
					Find a Doctor
				</button>
				<button on:click={() => goto('/dashboard')} class="back-link">
					← Back to Dashboard
				</button>
			</div>
		{:else}
			<!-- Chat Header -->
			<div class="chat-header">
				<button on:click={() => goto('/dashboard')} class="back-button" title="Back to Dashboard">
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
				</button>
				<div class="doctor-avatar">
					<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
				</div>
				<div class="doctor-details">
					<h2>{doctorInfo.name}</h2>
					<p class="status-text">
						<span class="status-indicator"></span>
						Healthcare Provider
					</p>
				</div>
			</div>
			
			<!-- Messages Area -->
			<div class="messages-area">
				{#if conversation.length === 0}
					<div class="empty-state">
						<div class="empty-icon">💬</div>
						<h3>Start Your Conversation</h3>
						<p>Send a message to connect with your healthcare provider</p>
					</div>
				{:else}
					<div class="messages-scroll">
						{#each conversation as msg, index}
							{@const showDate = index === 0 || new Date(conversation[index-1].created_at).toDateString() !== new Date(msg.created_at).toDateString()}
							
							{#if showDate}
								<div class="date-divider">
									<span>{new Date(msg.created_at).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}</span>
								</div>
							{/if}
							
							<div class="message-row {msg.sender_type === 'patient' ? 'sent' : 'received'}">
								{#if msg.sender_type === 'doctor'}
									<div class="message-avatar">
										<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
									</div>
								{/if}
								
								<div class="message-bubble">
									{#if msg.subject}
										<div class="message-subject">{msg.subject}</div>
									{/if}
									<div class="message-text">{msg.message}</div>
									<div class="message-meta">
										<span class="message-time">
											{new Date(msg.created_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}
										</span>
										{#if msg.sender_type === 'patient'}
											<span class="read-indicator" class:read={msg.is_read}>
												{#if msg.is_read}
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
			
			<!-- Message Input -->
			<div class="message-input-container">
				{#if newSubject !== ''}
					<div class="subject-pill">
						<span>📌 {newSubject}</span>
						<button on:click={() => newSubject = ''} class="remove-subject">×</button>
					</div>
				{/if}
				<div class="input-wrapper">
					<button class="attachment-btn" on:click={() => {
						const show = newSubject === '';
						if (show) {
							newSubject = '';
							setTimeout(() => {
							const input = document.querySelector('.subject-input-inline');
							if (input instanceof HTMLElement) input.focus();
							}, 100);
						}
					}} title="Add subject">
						<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
					</button>
					
					{#if newSubject === '' && conversation.length > 0}
						<input
							type="text"
							class="subject-input-inline"
							placeholder="Subject (optional)"
							bind:value={newSubject}
							on:blur={() => {
								if (!newSubject.trim()) newSubject = '';
							}}
						/>
					{:else}
						<textarea
							placeholder="Type your message..."
							bind:value={newMessage}
							rows="1"
							on:input={(e) => {
								const target = e.target;
								if (target instanceof HTMLTextAreaElement) {
									target.style.height = 'auto';
									target.style.height = Math.min(target.scrollHeight, 120) + 'px';
								}
							}}
							on:keydown={(e) => {
								if (e.key === 'Enter' && !e.shiftKey) {
									e.preventDefault();
									sendMessage();
								}
							}}
							class="message-textarea"
						></textarea>
					{/if}
					
					<button
						class="send-button"
						on:click={sendMessage}
						disabled={!newMessage.trim() || sendingMessage}
						title="Send message (Enter)"
					>
						{#if sendingMessage}
							<div class="sending-spinner"></div>
						{:else}
							<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
						{/if}
					</button>
				</div>
				<div class="input-hint">Press Enter to send • Shift+Enter for new line</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.messages-page {
		width: 100%;
		height: 100vh;
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
	
	/* Loading State */
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
		to { transform: rotate(360deg); }
	}
	
	.loading-state p {
		color: #666;
		font-size: 1.1rem;
	}
	
	/* No Doctor Card */
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
	
	/* Chat Header */
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
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	
	/* Messages Area */
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
	
	/* Empty State */
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
	
	/* Date Divider */
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
	
	/* Message Row */
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
	
	/* Message Bubble */
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
	
	/* Message Input Container */
	.message-input-container {
		background: #ffffff;
		border-top: 1px solid #e5e7eb;
		padding: 1rem 1.5rem;
		flex-shrink: 0;
	}
	
	.subject-pill {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: #ede9fe;
		color: #5b21b6;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		margin-bottom: 0.75rem;
		font-size: 0.875rem;
	}
	
	.remove-subject {
		background: none;
		border: none;
		color: #5b21b6;
		font-size: 1.5rem;
		cursor: pointer;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition: background 0.2s;
	}
	
	.remove-subject:hover {
		background: rgba(0, 0, 0, 0.1);
	}
	
	.input-wrapper {
		display: flex;
		align-items: flex-end;
		gap: 0.75rem;
		background: #f3f4f6;
		border-radius: 24px;
		padding: 0.5rem;
	}
	
	.attachment-btn {
		background: none;
		border: none;
		color: #6b7280;
		cursor: pointer;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		flex-shrink: 0;
	}
	
	.attachment-btn:hover {
		background: #e5e7eb;
		color: #667eea;
	}
	
	.subject-input-inline {
		flex: 1;
		border: none;
		background: transparent;
		padding: 0.625rem 0.5rem;
		font-size: 0.95rem;
		font-family: inherit;
		outline: none;
	}
	
	.message-textarea {
		flex: 1;
		border: none;
		background: transparent;
		padding: 0.625rem 0.5rem;
		font-size: 0.95rem;
		font-family: inherit;
		resize: none;
		outline: none;
		max-height: 120px;
		overflow-y: auto;
	}
	
	.message-textarea::-webkit-scrollbar {
		width: 4px;
	}
	
	.message-textarea::-webkit-scrollbar-thumb {
		background: #d1d5db;
		border-radius: 2px;
	}
	
	.send-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border: none;
		color: white;
		cursor: pointer;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		flex-shrink: 0;
	}
	
	.send-button:hover:not(:disabled) {
		transform: scale(1.1);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}
	
	.send-button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
	
	.sending-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	
	.input-hint {
		font-size: 0.75rem;
		color: #9ca3af;
		margin-top: 0.5rem;
		text-align: center;
	}
	
	/* Responsive Design */
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
		
		.chat-header {
			padding: 1rem;
		}
	}
</style>
