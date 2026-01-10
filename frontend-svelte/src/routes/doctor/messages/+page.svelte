<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
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
	
	const unsubscribe = user.subscribe(value => {
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
		try {
			const response = await api.get(`/api/doctor/${userData.id}/messages`);
			messages = response.data.messages;
			unreadCount = response.data.unread_count;
			loading = false;
		} catch (err) {
			console.error('Failed to load messages:', err);
			loading = false;
		}
	}
	
	async function loadConversation(patientId) {
		try {
			const response = await api.get(`/api/doctor/${userData.id}/messages/conversation/${patientId}`);
			conversation = response.data.messages;
			selectedPatient = {
				id: patientId,
				name: response.data.patient_name
			};
			
			// Mark unread messages as read
			const unreadMessages = conversation.filter(m => 
				!m.is_read && m.recipient_id === userData.id
			);
			
			for (const msg of unreadMessages) {
				await api.post(`/api/doctor/${userData.id}/messages/${msg.id}/mark-read`);
			}
			
			await loadMessages(); // Refresh to update unread count
		} catch (err) {
			console.error('Failed to load conversation:', err);
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
		} catch (err) {
			alert('Failed to send message: ' + (err.response?.data?.detail || 'Unknown error'));
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
		} else if (diffDays === 1) {
			return 'Yesterday';
		} else if (diffDays < 7) {
			return date.toLocaleDateString([], { weekday: 'short' });
		} else {
			return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
		}
	}
	
	function getUniquePatients() {
		const patientsMap = new Map();
		
		messages.forEach(msg => {
			let patientId, patientName, lastMessage, timestamp, hasUnread;
			
			if (msg.sender_type === 'patient') {
				patientId = msg.sender_id;
				patientName = msg.sender_name;
			} else {
				patientId = msg.recipient_id;
				patientName = msg.recipient_name;
			}
			
			if (!patientsMap.has(patientId)) {
				hasUnread = msg.sender_type === 'patient' && !msg.is_read;
				patientsMap.set(patientId, {
					id: patientId,
					name: patientName,
					lastMessage: msg.message,
					timestamp: msg.created_at,
					hasUnread: hasUnread
				});
			}
		});
		
		return Array.from(patientsMap.values());
	}
</script>

<div class="messaging-container">
	<div class="sidebar">
		<div class="sidebar-header">
			<button on:click={() => goto('/doctor/dashboard')} class="back-btn">
				← Dashboard
			</button>
			<h2>Messages</h2>
			{#if unreadCount > 0}
				<span class="unread-badge">{unreadCount}</span>
			{/if}
		</div>
		
		{#if loading}
			<div class="loading-sidebar">Loading messages...</div>
		{:else if getUniquePatients().length === 0}
			<div class="no-messages">No messages yet</div>
		{:else}
			<div class="patient-list">
				{#each getUniquePatients() as patient}
					<button
						class="patient-item {selectedPatient?.id === patient.id ? 'active' : ''} {patient.hasUnread ? 'unread' : ''}"
						on:click={() => loadConversation(patient.id)}
					>
						<div class="patient-info">
							<div class="patient-name">{patient.name}</div>
							<div class="last-message">{patient.lastMessage.substring(0, 50)}{patient.lastMessage.length > 50 ? '...' : ''}</div>
						</div>
						<div class="message-meta">
							<span class="timestamp">{formatDate(patient.timestamp)}</span>
							{#if patient.hasUnread}
								<span class="unread-dot"></span>
							{/if}
						</div>
					</button>
				{/each}
			</div>
		{/if}
	</div>
	
	<div class="conversation-area">
		{#if !selectedPatient}
			<div class="no-selection">
				<h3>Select a patient to view conversation</h3>
				<p>Choose a patient from the list to start messaging</p>
			</div>
		{:else}
			<div class="conversation-header">
				<h3>{selectedPatient.name}</h3>
			</div>
			
			<div class="messages-list">
				{#each conversation as msg}
					<div class="message-bubble {msg.sender_type === 'doctor' ? 'sent' : 'received'}">
						{#if msg.subject}
							<div class="message-subject">{msg.subject}</div>
						{/if}
						<div class="message-content">{msg.message}</div>
						<div class="message-timestamp">
							{new Date(msg.created_at).toLocaleString()}
							{#if msg.sender_type === 'doctor' && msg.is_read}
								<span class="read-indicator">✓✓</span>
							{/if}
						</div>
					</div>
				{/each}
			</div>
			
			<div class="message-composer">
				<input
					type="text"
					placeholder="Subject (optional)"
					bind:value={newSubject}
					class="subject-input"
				/>
				<div class="compose-row">
					<textarea
						placeholder="Type your message..."
						bind:value={newMessage}
						rows="3"
						on:keydown={(e) => {
							if (e.key === 'Enter' && !e.shiftKey) {
								e.preventDefault();
								sendMessage();
							}
						}}
					></textarea>
					<button
						class="send-btn"
						on:click={sendMessage}
						disabled={!newMessage.trim() || sendingMessage}
					>
						{sendingMessage ? 'Sending...' : 'Send'}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.messaging-container {
		display: grid;
		grid-template-columns: 350px 1fr;
		height: 100vh;
		background: #f5f5f5;
	}
	
	.sidebar {
		background: white;
		border-right: 1px solid #e0e0e0;
		display: flex;
		flex-direction: column;
	}
	
	.sidebar-header {
		padding: 1.5rem;
		border-bottom: 1px solid #e0e0e0;
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.sidebar-header h2 {
		margin: 0;
		flex: 1;
		font-size: 1.5rem;
	}
	
	.back-btn {
		background: #f0f0f0;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.9rem;
	}
	
	.back-btn:hover {
		background: #e0e0e0;
	}
	
	.unread-badge {
		background: #ef4444;
		color: white;
		padding: 0.25rem 0.5rem;
		border-radius: 12px;
		font-size: 0.85rem;
		font-weight: 600;
	}
	
	.patient-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.patient-item {
		width: 100%;
		padding: 1rem;
		border: none;
		border-bottom: 1px solid #f0f0f0;
		background: white;
		cursor: pointer;
		text-align: left;
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		transition: background 0.2s;
	}
	
	.patient-item:hover {
		background: #f9fafb;
	}
	
	.patient-item.active {
		background: #eff6ff;
		border-left: 3px solid #3b82f6;
	}
	
	.patient-item.unread {
		background: #fef3c7;
	}
	
	.patient-info {
		flex: 1;
	}
	
	.patient-name {
		font-weight: 600;
		margin-bottom: 0.25rem;
		color: #333;
	}
	
	.last-message {
		font-size: 0.85rem;
		color: #666;
	}
	
	.message-meta {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.25rem;
	}
	
	.timestamp {
		font-size: 0.75rem;
		color: #999;
	}
	
	.unread-dot {
		width: 10px;
		height: 10px;
		background: #ef4444;
		border-radius: 50%;
	}
	
	.loading-sidebar, .no-messages {
		padding: 2rem;
		text-align: center;
		color: #999;
	}
	
	.conversation-area {
		display: flex;
		flex-direction: column;
		background: #fafafa;
	}
	
	.no-selection {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		color: #999;
	}
	
	.conversation-header {
		background: white;
		padding: 1.5rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.conversation-header h3 {
		margin: 0;
		font-size: 1.25rem;
	}
	
	.messages-list {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.message-bubble {
		max-width: 70%;
		padding: 1rem;
		border-radius: 12px;
		background: white;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
	}
	
	.message-bubble.sent {
		align-self: flex-end;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}
	
	.message-bubble.received {
		align-self: flex-start;
		background: white;
	}
	
	.message-subject {
		font-weight: 600;
		margin-bottom: 0.5rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(0, 0, 0, 0.1);
	}
	
	.message-content {
		margin-bottom: 0.5rem;
		white-space: pre-wrap;
		word-wrap: break-word;
	}
	
	.message-timestamp {
		font-size: 0.75rem;
		opacity: 0.7;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.read-indicator {
		color: #4ade80;
	}
	
	.message-composer {
		background: white;
		border-top: 1px solid #e0e0e0;
		padding: 1rem;
	}
	
	.subject-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		margin-bottom: 0.5rem;
		font-size: 0.95rem;
	}
	
	.compose-row {
		display: flex;
		gap: 0.75rem;
	}
	
	.compose-row textarea {
		flex: 1;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		resize: none;
		font-family: inherit;
		font-size: 0.95rem;
	}
	
	.send-btn {
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
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
