<script>
	import { training } from '$lib/api';
	import { user } from '$lib/stores';
	import { goto } from '$app/navigation';
	
	let currentUser = null;
	let isOpen = false;
	let isMinimized = false;
	let loading = false;
	let message = '';
	let messageType = 'success'; // success, error, info
	let showTaskLauncher = false;
	let selectedDomain = null;
	let selectedDifficulty = 5; // Default difficulty (1-10)

	user.subscribe(value => {
		currentUser = value;
	});
	
	// Map domain display names to backend domain keys
	const domainKeyMap = {
		'Working Memory': 'working_memory',
		'Processing Speed': 'processing_speed',
		'Attention': 'attention',
		'Cognitive Flexibility': 'flexibility',
		'Executive Planning': 'planning',
		'Visual Scanning': 'visual_scanning'
	};

	// Route mapping for all tasks - maps task code to actual route
	const taskRoutes = {
		// Working Memory
		'n_back': '/baseline/tasks/working-memory',
		'dual-n-back': '/training/dual-n-back',
		'digit-span': '/training/digit-span',
		'spatial-span': '/training/spatial-span',
		'letter-number-sequencing': '/training/letter-number-sequencing',
		'operation-span': '/training/operation-span',

		// Processing Speed
		'simple_reaction': '/baseline/tasks/processing-speed',
		'sdmt': '/training/sdmt',
		'pasat': '/training/pasat',
		'inspection-time': '/training/inspection-time',
		'pattern-comparison': '/training/pattern-comparison',

		// Attention
		'gonogo': '/training/gonogo',
		'flanker': '/training/flanker',
		'stroop': '/training/stroop',

		// Cognitive Flexibility
		'dccs': '/training/dccs',
		'trail-making-a': '/training/trail-making-a',
		'trail-making-b': '/training/trail-making-b',
		'plus-minus': '/training/plus-minus',
		'wcst': '/training/wcst',

		// Executive Planning
		'tower-of-london': '/training/tower-of-london',
		'stockings-of-cambridge': '/training/stockings-of-cambridge',
		'twenty-questions': '/training/twenty-questions',
		'category-fluency': '/training/category-fluency',
		'verbal-fluency': '/training/verbal-fluency',

		// Visual Scanning
		'visual-search': '/training/visual-search',
		'cancellation-test': '/training/cancellation-test',
		'multiple-object-tracking': '/training/multiple-object-tracking',
		'useful-field-of-view': '/training/useful-field-of-view'
	};

	const tasksByDomain = {
		'Working Memory': [
			{ name: 'N-Back Test', code: 'n_back' },
			{ name: 'Dual N-Back', code: 'dual-n-back' },
			{ name: 'Digit Span', code: 'digit-span' },
			{ name: 'Spatial Span', code: 'spatial-span' },
			{ name: 'Letter-Number Sequencing', code: 'letter-number-sequencing' },
			{ name: 'Operation Span', code: 'operation-span' }
		],
		'Processing Speed': [
			{ name: 'Simple Reaction Time', code: 'simple_reaction' },
			{ name: 'SDMT', code: 'sdmt' },
			{ name: 'PASAT', code: 'pasat' },
			{ name: 'Inspection Time', code: 'inspection-time' },
			{ name: 'Pattern Comparison', code: 'pattern-comparison' }
		],
		'Attention': [
			{ name: 'Go/No-Go (CPT)', code: 'gonogo' },
			{ name: 'Flanker Task', code: 'flanker' },
			{ name: 'Stroop Test', code: 'stroop' }
		],
		'Cognitive Flexibility': [
			{ name: 'DCCS', code: 'dccs' },
			{ name: 'Trail Making A', code: 'trail-making-a' },
			{ name: 'Trail Making B', code: 'trail-making-b' },
			{ name: 'Plus-Minus Task', code: 'plus-minus' },
			{ name: 'Wisconsin Card Sort', code: 'wcst' }
		],
		'Executive Planning': [
			{ name: 'Tower of London', code: 'tower-of-london' },
			{ name: 'Stockings of Cambridge', code: 'stockings-of-cambridge' },
			{ name: '20 Questions', code: 'twenty-questions' },
			{ name: 'Category Fluency', code: 'category-fluency' },
			{ name: 'Verbal Fluency', code: 'verbal-fluency' }
		],
		'Visual Scanning': [
			{ name: 'Visual Search', code: 'visual-search' },
			{ name: 'Cancellation Test', code: 'cancellation-test' },
			{ name: 'Multiple Object Tracking', code: 'multiple-object-tracking' },
			{ name: 'Useful Field of View', code: 'useful-field-of-view' }
		]
	};

	function getTaskRoute(taskCode) {
		return taskRoutes[taskCode] || `/training/${taskCode}`;
	}

	async function launchTask(taskCode) {
		if (!currentUser) {
			showMessage('❌ Please log in first', 'error');
			return;
		}
		
		loading = true;

		try {
			// Ensure difficulty is a valid number between 1-10
			const validDifficulty = Math.max(1, Math.min(10, Number(selectedDifficulty) || 5));

			console.log('🎮 DevPanel - Launching task:', {
				taskCode,
				selectedDomain,
				selectedDifficulty_RAW: selectedDifficulty,
				selectedDifficulty_TYPE: typeof selectedDifficulty,
				validDifficulty,
				userId: currentUser.id
			});

			// Get the domain key for this task's domain
			const domainKey = domainKeyMap[selectedDomain];
			console.log('🗺️ DevPanel - Domain mapping:', { selectedDomain, domainKey });

			if (domainKey) {
				// Set difficulty via API before launching
				console.log(`📡 DevPanel - Calling API to set ${domainKey} difficulty to ${validDifficulty}`);

				const result = await training.dev.setDomainDifficulty(currentUser.id, domainKey, validDifficulty);

				console.log('✅ DevPanel - API Response:', result);
				console.log('📊 DevPanel - Difficulty change:', {
					domain: domainKey,
					from: result.old_difficulty,
					to: result.new_difficulty,
					wasSuccessful: result.success
				});

				showMessage(`🎯 Set ${selectedDomain} to Level ${validDifficulty}`, 'success');

				// Wait for the API to complete
				await new Promise(resolve => setTimeout(resolve, 500));
			} else {
				console.warn('⚠️ DevPanel - No domain key found for:', selectedDomain);
				showMessage(`⚠️ Warning: Domain ${selectedDomain} not mapped`, 'error');
			}

			const route = getTaskRoute(taskCode);
			console.log('🚀 DevPanel - Navigating to:', route, 'with difficulty:', validDifficulty);
			goto(`${route}?training=true&planId=1&taskId=${taskCode}_dev&difficulty=${validDifficulty}`);
		} catch (error) {
			console.error('❌ DevPanel - Failed to set difficulty:', error);
			showMessage(`❌ Failed to set difficulty: ${error.message}`, 'error');
			// Still navigate even if setting difficulty fails
			const route = getTaskRoute(taskCode);
			goto(`${route}?training=true&planId=1&taskId=${taskCode}_dev`);
		} finally {
			loading = false;
		}
	}

	function adjustDifficulty(delta) {
		selectedDifficulty = Math.max(1, Math.min(10, selectedDifficulty + delta));
	}

	function getDifficultyLabel(diff) {
		if (diff <= 2) return 'Very Easy';
		if (diff <= 4) return 'Easy';
		if (diff <= 6) return 'Medium';
		if (diff <= 8) return 'Hard';
		return 'Expert';
	}

	async function completeSingleSession() {
		if (!currentUser) return;
		loading = true;
		message = '';
		
		try {
			const result = await training.dev.completeSingleSession(currentUser.id);
			showMessage(`✅ ${result.message}! 🔥 ${result.current_streak} day streak`, 'success');
			
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
	
	function previewEmptyStates() {
		window.location.href = '/empty-states-preview';
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
		isMinimized = false;
	}
	
	function toggleMinimize() {
		isMinimized = !isMinimized;
	}
	
	function toggleTaskLauncher() {
		showTaskLauncher = !showTaskLauncher;
		selectedDomain = null; // Reset domain when closing
	}
	
	function selectDomain(domain) {
		selectedDomain = domain;
	}
	
	function backToDomains() {
		selectedDomain = null;
	}
</script>

<div class="dev-panel {isOpen ? 'open' : ''}">
	<button class="toggle-btn" on:click={togglePanel} title="Dev Tools">
		🛠️
	</button>
	
	{#if isOpen}
		<div class="panel-content" class:minimized={isMinimized}>
			<div class="panel-header">
				<h3>⚡ Dev Tools</h3>
				<div class="header-actions">
					<button class="minimize-btn" on:click={toggleMinimize} title={isMinimized ? 'Expand' : 'Minimize'}>
						{isMinimized ? '▲' : '▼'}
					</button>
					<button class="close-btn" on:click={togglePanel}>×</button>
				</div>
			</div>
			
			{#if !isMinimized}
			{#if message}
				<div class="message {messageType}">
					{message}
				</div>
			{/if}
			
			<!-- Game Launcher - Top Priority -->
			{#if showTaskLauncher}
			<div class="task-launcher">
				<!-- Difficulty Selector - Always visible -->
				<div class="difficulty-selector">
					<span class="diff-label">Difficulty:</span>
					<button class="diff-btn" on:click={() => adjustDifficulty(-1)} disabled={selectedDifficulty <= 1}>−</button>
					<span class="diff-value">{selectedDifficulty}</span>
					<button class="diff-btn" on:click={() => adjustDifficulty(1)} disabled={selectedDifficulty >= 10}>+</button>
					<span class="diff-level">({getDifficultyLabel(selectedDifficulty)})</span>
				</div>

				{#if !selectedDomain}
					<!-- Domain Selection -->
					<h4 style="margin: 0 0 8px 0; color: #333; font-size: 0.95rem;">Select Domain</h4>
					<div class="domain-grid">
						{#each Object.keys(tasksByDomain) as domain}
							<button 
								class="domain-btn" 
								on:click={() => selectDomain(domain)}
							>
								{domain}
							</button>
						{/each}
					</div>
				{:else}
					<!-- Task Selection -->
					<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
						<button class="back-btn" on:click={backToDomains}>← Back</button>
						<h4 style="margin: 0; color: #333; flex: 1; font-size: 0.9rem;">{selectedDomain}</h4>
					</div>
					<div class="tasks-list">
						{#each tasksByDomain[selectedDomain] as task}
							<button 
								class="task-btn" 
								on:click={() => launchTask(task.code)}
								disabled={loading}
							>
								{task.name}
							</button>
						{/each}
					</div>
				{/if}
			</div>
			{/if}
			
			<div class="section-divider">
				<button class="section-toggle" on:click={toggleTaskLauncher}>
					{showTaskLauncher ? '✕ Close' : '🎮 Go to Game Section'}
				</button>
			</div>
			
			<!-- Dev Actions -->
			<div class="buttons">
				<button class="dev-btn primary" on:click={completeSingleSession} disabled={loading}>
					<span class="icon">✅</span>
					<span class="text">
						<strong>Complete Session</strong>
						<small>Finish 1 session (4 tasks)</small>
					</span>
				</button>
				
				<button class="dev-btn primary" on:click={generateSessions} disabled={loading}>
					<span class="icon">📊</span>
					<span class="text">
						<strong>Generate Sessions</strong>
						<small>Add 3 test sessions (12 tasks)</small>
					</span>
				</button>
				
				<button class="dev-btn accent" on:click={setStreak} disabled={loading}>
					<span class="icon">🔥</span>
					<span class="text">
						<strong>Set 7-Day Streak</strong>
						<small>Test streak features</small>
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
			{/if}
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
		max-width: 380px;
		max-height: 85vh;
		overflow-y: auto;
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
	
	.header-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	
	.minimize-btn {
		background: none;
		border: none;
		font-size: 1.2rem;
		color: #999;
		cursor: pointer;
		line-height: 1;
		padding: 0;
		width: 25px;
		height: 25px;
		transition: color 0.2s;
	}
	
	.minimize-btn:hover {
		color: #667eea;
	}
	
	.panel-content.minimized {
		padding: 1rem 1.5rem;
	}
	
	.panel-content.minimized .buttons,
	.panel-content.minimized .message,
	.panel-content.minimized .info,
	.panel-content.minimized .task-launcher,
	.panel-content.minimized .section-divider {
		display: none;
	}
	
	.section-divider {
		margin: 1rem 0;
		text-align: center;
	}
	
	.section-toggle {
		width: 100%;
		padding: 0.75rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 600;
		transition: all 0.2s;
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
	}
	
	.section-toggle:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
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
	
	.dev-btn.preview {
		background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%);
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
	
	.task-launcher {
		margin-bottom: 1rem;
		padding: 0.75rem;
		background: #f8f9fa;
		border-radius: 8px;
	}

	.difficulty-selector {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
		padding: 0.6rem 0.75rem;
		background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
		border-radius: 8px;
		border: 1px solid #667eea30;
	}

	.diff-label {
		font-size: 0.85rem;
		font-weight: 600;
		color: #333;
	}

	.diff-btn {
		width: 28px;
		height: 28px;
		border: none;
		border-radius: 6px;
		background: #667eea;
		color: white;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.diff-btn:hover:not(:disabled) {
		background: #5a6fd6;
		transform: scale(1.1);
	}

	.diff-btn:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.diff-value {
		font-size: 1.1rem;
		font-weight: bold;
		color: #667eea;
		min-width: 24px;
		text-align: center;
	}

	.diff-level {
		font-size: 0.75rem;
		color: #666;
		margin-left: auto;
		font-style: italic;
	}

	.domain-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.4rem;
	}
	
	.domain-btn {
		padding: 0.6rem 0.5rem;
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.8rem;
		font-weight: 600;
		color: #333;
		transition: all 0.2s;
		text-align: center;
		line-height: 1.2;
	}
	
	.domain-btn:hover {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-color: #667eea;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}
	
	.back-btn {
		padding: 0.4rem 0.8rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.85rem;
		color: #667eea;
		font-weight: 500;
		transition: all 0.2s;
	}
	
	.back-btn:hover {
		background: #667eea;
		color: white;
		border-color: #667eea;
	}
	
	.tasks-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.4rem;
	}
	
	.task-btn {
		padding: 0.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.75rem;
		font-weight: 500;
		color: #333;
		transition: all 0.2s;
		text-align: center;
		line-height: 1.3;
	}
	
	.tasks-list::-webkit-scrollbar {
		width: 6px;
	}
	
	.tasks-list::-webkit-scrollbar-track {
		background: #f1f1f1;
		border-radius: 3px;
	}
	
	.tasks-list::-webkit-scrollbar-thumb {
		background: #667eea;
		border-radius: 3px;
	}
	
	.tasks-list::-webkit-scrollbar-thumb:hover {
		background: #764ba2;
	}
	
	/* Removed duplicate - task-btn styles are above */
	
	.task-btn:hover:not(:disabled) {
		background: #667eea;
		color: white;
		border-color: #667eea;
		transform: translateY(-2px);
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
	}
	
	.task-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
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
