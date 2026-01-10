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
			
			// First check if patient has an assigned doctor
			const assignmentResponse = await api.get(`/api/doctor/patient/${userData.id}/assigned-doctor`);
			console.log('Assignment check:', assignmentResponse.data);
			
			if (!assignmentResponse.data.assigned) {
				console.log('No doctor assigned according to assignment check');
				doctorInfo = null;
				loading = false;
				return;
			}
			
			// Now load the conversation
			const response = await api.get(`/api/patient/${userData.id}/messages/with-doctor`);
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
					await api.post(`/api/patient/${userData.id}/messages/${msg.id}/mark-read`);
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
			await api.post(`/api/patient/${userData.id}/messages/send`, {
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
	<div class="header">
		<button on:click={() => goto('/dashboard')} class="back-btn">
			← Back to Dashboard
		</button>
		<h1>Messages with Your Doctor</h1>
	</div>
	
	{#if loading}
		<div class="loading">Loading messages...</div>
	{:else if !doctorInfo}
		<div class="no-doctor">
			<h2>No Doctor Assigned</h2>
			<p>You need to be assigned to a doctor to use messaging.</p>
			<button on:click={() => goto('/find-doctor')} class="btn-primary">
				Find a Doctor
			</button>
		</div>
	{:else}
		<div class="messaging-container">
			<div class="conversation-header">
				<div class="doctor-info">
					<h2>{doctorInfo.name}</h2>
					<p>Your assigned healthcare provider</p>
				</div>
			</div>
			
			<div class="messages-list">
				{#if conversation.length === 0}
					<div class="no-messages">
						<p>No messages yet. Start a conversation with your doctor!</p>
					</div>
				{:else}
					{#each conversation as msg}
						<div class="message-bubble {msg.sender_type === 'patient' ? 'sent' : 'received'}">
							<div class="message-header">
								<span class="sender-name">{msg.sender_name}</span>
								<span class="message-timestamp">{formatDate(msg.created_at)}</span>
							</div>
							{#if msg.subject}
								<div class="message-subject">{msg.subject}</div>
							{/if}
							<div class="message-content">{msg.message}</div>
							{#if msg.sender_type === 'patient' && msg.is_read}
								<div class="read-status">✓✓ Read</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
			
			<div class="message-composer">
				<h3>Send a Message</h3>
				<input
					type="text"
					placeholder="Subject (optional)"
					bind:value={newSubject}
					class="subject-input"
				/>
				<textarea
					placeholder="Type your message to your doctor..."
					bind:value={newMessage}
					rows="4"
					on:keydown={(e) => {
						if (e.key === 'Enter' && e.ctrlKey) {
							sendMessage();
						}
					}}
				></textarea>
				<div class="composer-footer">
					<span class="hint">Press Ctrl+Enter to send</span>
					<button
						class="send-btn"
						on:click={sendMessage}
						disabled={!newMessage.trim() || sendingMessage}
					>
						{sendingMessage ? 'Sending...' : 'Send Message'}
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.messages-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: #f5f5f5;
	}
	
	.header {
		margin-bottom: 2rem;
	}
	
	.header h1 {
		margin-top: 1rem;
		color: #333;
	}
	
	.back-btn {
		background: #f0f0f0;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.95rem;
		transition: background 0.3s;
	}
	
	.back-btn:hover {
		background: #e0e0e0;
	}
	
	.loading {
		text-align: center;
		padding: 3rem;
		font-size: 1.1rem;
		color: #666;
	}
	
	.no-doctor {
		background: white;
		padding: 3rem;
		border-radius: 12px;
		text-align: center;
	}
	
	.no-doctor h2 {
		color: #666;
		margin-bottom: 1rem;
	}
	
	.no-doctor p {
		color: #999;
		margin-bottom: 2rem;
	}
	
	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 2rem;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s;
	}
	
	.btn-primary:hover {
		transform: translateY(-2px);
	}
	
	.messaging-container {
		background: white;
		border-radius: 12px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
		overflow: hidden;
	}
	
	.conversation-header {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 2rem;
	}
	
	.doctor-info h2 {
		margin: 0 0 0.5rem 0;
		font-size: 1.75rem;
	}
	
	.doctor-info p {
		margin: 0;
		opacity: 0.9;
	}
	
	.messages-list {
		padding: 2rem;
		max-height: 500px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		background: #fafafa;
	}
	
	.no-messages {
		text-align: center;
		padding: 3rem;
		color: #999;
	}
	
	.message-bubble {
		max-width: 75%;
		padding: 1rem;
		border-radius: 12px;
		background: white;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.message-bubble.sent {
		align-self: flex-end;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}
	
	.message-bubble.received {
		align-self: flex-start;
		background: white;
		border-left: 3px solid #667eea;
	}
	
	.message-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
		font-size: 0.85rem;
	}
	
	.sender-name {
		font-weight: 600;
	}
	
	.message-timestamp {
		opacity: 0.7;
		font-size: 0.75rem;
	}
	
	.message-subject {
		font-weight: 600;
		margin-bottom: 0.5rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}
	
	.message-bubble.sent .message-subject {
		border-bottom-color: rgba(255, 255, 255, 0.3);
	}
	
	.message-content {
		white-space: pre-wrap;
		word-wrap: break-word;
		line-height: 1.6;
	}
	
	.read-status {
		margin-top: 0.5rem;
		font-size: 0.75rem;
		opacity: 0.7;
		text-align: right;
		color: #4ade80;
	}
	
	.message-composer {
		padding: 2rem;
		border-top: 2px solid #f0f0f0;
	}
	
	.message-composer h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.25rem;
	}
	
	.subject-input {
		width: 100%;
		padding: 0.75rem;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		margin-bottom: 0.75rem;
		font-size: 0.95rem;
		font-family: inherit;
	}
	
	.subject-input:focus {
		outline: none;
		border-color: #667eea;
	}
	
	textarea {
		width: 100%;
		padding: 0.75rem;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		resize: vertical;
		font-family: inherit;
		font-size: 0.95rem;
		margin-bottom: 0.75rem;
	}
	
	textarea:focus {
		outline: none;
		border-color: #667eea;
	}
	
	.composer-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.hint {
		font-size: 0.85rem;
		color: #999;
	}
	
	.send-btn {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 2rem;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s;
	}
	
	.send-btn:hover:not(:disabled) {
		transform: translateY(-2px);
	}
	
	.send-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
