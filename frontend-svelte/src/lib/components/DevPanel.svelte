<script>
	import { training } from '$lib/api';
	import { user } from '$lib/stores';
	
	let currentUser = null;
	let isOpen = false;
	let loading = false;
	let message = '';
	let messageType = 'success'; // success, error, info
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	async function completeSession() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			const result = await training.dev.completeSession(currentUser.id);
			showMessage(`✅ ${result.message}! Session ${result.session_complete ? 'complete' : 'in progress'}`, 'success');
			
			// Reload page to show updates
			setTimeout(() => window.location.reload(), 1500);
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function generateSessions() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			const result = await training.dev.generateSessions(currentUser.id, 3);
			showMessage(`✅ ${result.message}!`, 'success');
			
			setTimeout(() => window.location.reload(), 1500);
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function setStreak() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			const result = await training.dev.setStreak(currentUser.id, 7);
			showMessage(`✅ ${result.message}`, 'success');
			
			setTimeout(() => window.location.reload(), 1500);
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function clearAll() {
		if (!currentUser) return;
		if (!confirm('Clear all training sessions? This cannot be undone!')) return;
		
		loading = true;
		message = '';
		
		try {
			const result = await training.dev.clearSessions(currentUser.id);
			showMessage(`✅ ${result.message}`, 'success');
			
			setTimeout(() => window.location.reload(), 1500);
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function checkBadges() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			const result = await training.dev.checkBadges(currentUser.id);
			
			if (result.newly_earned.length > 0) {
				const badgeNames = result.new_badge_details.map(b => `${b.icon} ${b.name}`).join(', ');
				showMessage(`🎉 ${result.newly_earned.length} new badges! ${badgeNames}`, 'success');
			} else {
				showMessage(`✓ Badge check complete. Total: ${result.total_earned} badges`, 'info');
			}
			
			setTimeout(() => window.location.reload(), 2500);
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function generateWeekData() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			// Generate 10 sessions spread over 7 days
			const result = await training.dev.generateSessions(currentUser.id, 10);
			showMessage(`✅ Generated ${result.sessions_generated} sessions over 7 days!`, 'success');
			
			setTimeout(() => window.location.reload(), 1500);
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function viewWeeklySummary() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			const summary = await training.getWeeklySummary(currentUser.id);
			
			// Format the data for display
			const info = [
				`📊 ${summary.total_sessions} sessions`,
				`⭐ ${summary.average_score.toFixed(1)} avg score`,
				`🎯 ${summary.average_accuracy.toFixed(1)}% accuracy`,
				`⏱️ ${summary.total_time_minutes} min total`,
				`🔥 ${summary.current_streak} day streak`
			].join(' • ');
			
			console.log('📈 Weekly Summary Data:', summary);
			showMessage(`📈 Last 7 Days: ${info}`, 'info');
		} catch (error) {
			showMessage(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	async function testWeeklySummaryPhase() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			// Step 1: Generate test data
			showMessage('⏳ Step 1/3: Generating test sessions...', 'info');
			const genResult = await training.dev.generateSessions(currentUser.id, 10);
			
			await new Promise(resolve => setTimeout(resolve, 500));
			
			// Step 2: Fetch weekly summary
			showMessage('⏳ Step 2/3: Fetching weekly summary...', 'info');
			const summary = await training.getWeeklySummary(currentUser.id);
			
			// Step 3: Validate data
			showMessage('⏳ Step 3/3: Validating data...', 'info');
			await new Promise(resolve => setTimeout(resolve, 500));
			
			const issues = [];
			if (summary.total_sessions === 0) issues.push('No sessions found');
			if (summary.average_score === 0) issues.push('Score is 0');
			if (!summary.daily_activity || summary.daily_activity.length !== 7) issues.push('Daily activity missing');
			
			if (issues.length > 0) {
				showMessage(`⚠️ Issues found: ${issues.join(', ')}`, 'error');
				return;
			}
			
			// Success - navigate to session-summary to view
			showMessage(`✅ Phase 5 Test Passed! ${summary.total_sessions} sessions, ${summary.average_score.toFixed(1)} avg score`, 'success');
			
			console.log('✅ Weekly Summary Test Results:', {
				sessions_generated: genResult.sessions_generated,
				weekly_summary: summary,
				validation: 'PASSED'
			});
			
			setTimeout(() => {
				window.location.href = '/session-summary';
			}, 2000);
			
		} catch (error) {
			console.error('❌ Phase 5 Test Failed:', error);
			showMessage(`❌ Test Failed: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	}
	
	function showMessage(msg, type) {
		message = msg;
		messageType = type;
		setTimeout(() => {
			message = '';
		}, 3000);
	}
	
	function togglePanel() {
		isOpen = !isOpen;
	}
</script>

<div class="dev-panel {isOpen ? 'open' : ''}">
	<button class="toggle-btn" on:click={togglePanel} title="Dev Tools">
		🛠️
	</button>
	
	{#if isOpen}
		<div class="panel-content">
			<div class="panel-header">
				<h3>⚡ Dev Tools</h3>
				<button class="close-btn" on:click={togglePanel}>×</button>
			</div>
			
			{#if message}
				<div class="message {messageType}">
					{message}
				</div>
			{/if}
			
			<div class="buttons">
				<button class="dev-btn primary" on:click={completeSession} disabled={loading}>
					<span class="icon">✓</span>
					<span class="text">
						<strong>Complete Session</strong>
						<small>Finish current 4 tasks</small>
					</span>
				</button>
				
				<button class="dev-btn secondary" on:click={generateSessions} disabled={loading}>
					<span class="icon">📊</span>
					<span class="text">
						<strong>Generate 3 Sessions</strong>
						<small>Add test data (12 tasks)</small>
					</span>
				</button>
				
				<button class="dev-btn accent" on:click={setStreak} disabled={loading}>
					<span class="icon">🔥</span>
					<span class="text">
						<strong>Set 7-Day Streak</strong>
						<small>Test streak features</small>
					</span>
				</button>
				
				<button class="dev-btn badge" on:click={checkBadges} disabled={loading}>
					<span class="icon">🏆</span>
					<span class="text">
						<strong>Check Badges</strong>
						<small>Award eligible badges</small>
					</span>
				</button>
				
				<div class="separator">Weekly Summary Testing</div>
				
				<button class="dev-btn test" on:click={testWeeklySummaryPhase} disabled={loading}>
					<span class="icon">🧪</span>
					<span class="text">
						<strong>Test Phase 5 ✨</strong>
						<small>Full test + validation</small>
					</span>
				</button>
				
				<button class="dev-btn weekly" on:click={generateWeekData} disabled={loading}>
					<span class="icon">📅</span>
					<span class="text">
						<strong>Generate Week Data</strong>
						<small>10 sessions over 7 days</small>
					</span>
				</button>
				
				<button class="dev-btn info" on:click={viewWeeklySummary} disabled={loading}>
					<span class="icon">📈</span>
					<span class="text">
						<strong>View Weekly Data</strong>
						<small>Check API response</small>
					</span>
				</button>
				
				<button class="dev-btn danger" on:click={clearAll} disabled={loading}>
					<span class="icon">🗑️</span>
					<span class="text">
						<strong>Clear All Data</strong>
						<small>Reset to fresh start</small>
					</span>
				</button>
			</div>
			
			<div class="info">
				<small>💡 Quick test tools for development</small>
			</div>
		</div>
	{/if}
</div>

<style>
	.dev-panel {
		position: fixed;
		bottom: 20px;
		right: 20px;
		z-index: 9999;
		font-family: system-ui, -apple-system, sans-serif;
	}
	
	.toggle-btn {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		font-size: 1.8rem;
		cursor: pointer;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
		transition: all 0.3s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.toggle-btn:hover {
		transform: scale(1.1) rotate(15deg);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
	}
	
	.dev-panel.open .toggle-btn {
		display: none;
	}
	
	.panel-content {
		background: white;
		border-radius: 15px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
		padding: 1.5rem;
		min-width: 320px;
		max-width: 400px;
		animation: slideIn 0.3s ease;
	}
	
	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 2px solid #f0f0f0;
	}
	
	.panel-header h3 {
		margin: 0;
		color: #333;
		font-size: 1.2rem;
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 2rem;
		color: #999;
		cursor: pointer;
		line-height: 1;
		padding: 0;
		width: 30px;
		height: 30px;
		transition: color 0.2s;
	}
	
	.close-btn:hover {
		color: #333;
	}
	
	.message {
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
		font-weight: 500;
	}
	
	.message.success {
		background: #d4edda;
		color: #155724;
		border: 1px solid #c3e6cb;
	}
	
	.message.error {
		background: #f8d7da;
		color: #721c24;
		border: 1px solid #f5c6cb;
	}
	
	.message.info {
		background: #d1ecf1;
		color: #0c5460;
		border: 1px solid #bee5eb;
	}
	
	.buttons {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.separator {
		margin-top: 0.5rem;
		padding: 0.5rem 0;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		color: #666;
		border-top: 1px solid #e0e0e0;
		letter-spacing: 0.5px;
	}
	
	.dev-btn {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border: none;
		border-radius: 10px;
		cursor: pointer;
		transition: all 0.2s;
		text-align: left;
		font-family: inherit;
	}
	
	.dev-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}
	
	.dev-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.dev-btn .icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}
	
	.dev-btn .text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		flex: 1;
	}
	
	.dev-btn strong {
		font-size: 0.95rem;
		display: block;
	}
	
	.dev-btn small {
		font-size: 0.8rem;
		opacity: 0.8;
		font-weight: normal;
	}
	
	.dev-btn.primary {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
	}
	
	.dev-btn.secondary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}
	
	.dev-btn.accent {
		background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
		color: white;
	}
	
	.dev-btn.badge {
		background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
		color: white;
	}
	
	.dev-btn.test {
		background: linear-gradient(135deg, #00e676 0%, #00c853 100%);
		color: white;
		font-weight: 600;
		box-shadow: 0 4px 15px rgba(0, 230, 118, 0.3);
	}
	
	.dev-btn.test:hover:not(:disabled) {
		box-shadow: 0 6px 20px rgba(0, 230, 118, 0.4);
	}
	
	.dev-btn.weekly {
		background: linear-gradient(135deg, #00bcd4 0%, #0097a7 100%);
		color: white;
	}
	
	.dev-btn.info {
		background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
		color: white;
	}
	
	.dev-btn.danger {
		background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
		color: white;
	}
	
	.info {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #f0f0f0;
		text-align: center;
	}
	
	.info small {
		color: #666;
		font-size: 0.85rem;
	}
	
	@media (max-width: 480px) {
		.panel-content {
			min-width: 280px;
			max-width: calc(100vw - 40px);
		}
		
		.dev-btn {
			padding: 0.75rem;
		}
		
		.dev-btn .icon {
			font-size: 1.2rem;
		}
		
		.dev-btn strong {
			font-size: 0.9rem;
		}
		
		.dev-btn small {
			font-size: 0.75rem;
		}
	}
</style>
