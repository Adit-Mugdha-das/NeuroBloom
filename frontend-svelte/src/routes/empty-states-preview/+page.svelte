<script>
	import { goto } from '$app/navigation';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
</script>

<div class="preview-container">
	<div class="preview-header">
		<h1>🎨 Phase 6: Empty States Preview</h1>
		<p>All empty states and loading skeletons without clearing your data</p>
		<button class="back-btn" on:click={() => goto('/dashboard')}>← Back to Dashboard</button>
	</div>
	
	<div class="preview-grid">
		<!-- Progress Page Empty State -->
		<div class="preview-section">
			<h3>Progress Page - No Data</h3>
			<div class="preview-wrapper gradient-bg">
				<EmptyState 
					icon="📊"
					title="Start Your Progress Journey"
					message="Complete your first training session to see detailed analytics, trends, and badges!"
					actionText="Begin Training"
					actionLink="/training"
					tip="Consistent training leads to measurable cognitive improvements"
					variant="large"
				/>
			</div>
		</div>
		
		<!-- Session Summary Empty State -->
		<div class="preview-section">
			<h3>Session Summary - No Session</h3>
			<div class="preview-wrapper purple-gradient-bg">
				<EmptyState 
					icon="🎯"
					title="No Session Data"
					message="Complete a training session to see your celebration summary here!"
					actionText="Start Training"
					actionLink="/training"
					tip="Each session includes 4 cognitive tasks designed to challenge your brain"
				/>
			</div>
		</div>
		
		<!-- Weekly Summary Empty State -->
		<div class="preview-section">
			<h3>Weekly Summary - Less than 7 Days</h3>
			<div class="preview-wrapper">
				<EmptyState 
					icon="📅"
					title="Build Your Weekly Streak"
					message="Train for 7 days to unlock your weekly summary with insights and progress tracking!"
					actionText="Start Training"
					actionLink="/training"
					tip="Training multiple days per week shows better cognitive improvements"
					variant="compact"
				/>
			</div>
		</div>
		
		<!-- Badges Empty State -->
		<div class="preview-section">
			<h3>Badges - No Badges Earned</h3>
			<div class="preview-wrapper">
				<EmptyState 
					icon="🎯"
					title="Start Earning Badges!"
					message="Complete training sessions to unlock your first achievement badge!"
					actionText="Start Training"
					actionLink="/training"
					tip="Badges track your progress, consistency, and mastery across all cognitive domains"
					variant="compact"
				/>
			</div>
		</div>
		
		<!-- Performance Trends Empty State -->
		<div class="preview-section">
			<h3>Performance Trends - Not Enough Data</h3>
			<div class="preview-wrapper">
				<EmptyState 
					icon="📈"
					title="Track Your Progress"
					message="Complete multiple training sessions to unlock your performance trends graph and see how you improve over time!"
					actionText="Start Training"
					actionLink="/training"
					tip="Trends become visible after 3+ sessions"
					variant="compact"
				/>
			</div>
		</div>
		
		<!-- Loading Skeleton - Card Variant -->
		<div class="preview-section">
			<h3>Loading Skeleton - Card Grid</h3>
			<div class="preview-wrapper">
				<LoadingSkeleton variant="card" count={4} />
			</div>
		</div>
		
		<!-- Loading Skeleton - List Variant -->
		<div class="preview-section">
			<h3>Loading Skeleton - List Items</h3>
			<div class="preview-wrapper">
				<LoadingSkeleton variant="list" count={3} />
			</div>
		</div>
		
		<!-- Loading Skeleton - Default Variant -->
		<div class="preview-section">
			<h3>Loading Skeleton - Block</h3>
			<div class="preview-wrapper">
				<LoadingSkeleton variant="default" count={2} />
			</div>
		</div>
	</div>
	
	<div class="preview-footer">
		<h3>✅ Phase 6 Features Demonstrated:</h3>
		<ul>
			<li>✨ Animated icons with bounce effect</li>
			<li>🎨 Gradient backgrounds (3 variants: default, compact, large)</li>
			<li>💡 Glass-morphism tip cards</li>
			<li>🔘 Interactive call-to-action buttons with hover effects</li>
			<li>⚡ Shimmer loading skeletons (3 variants: card, list, block)</li>
			<li>📱 Fully responsive design</li>
			<li>🎯 Context-specific messaging for each empty state</li>
			<li>✨ Professional polish throughout</li>
		</ul>
	</div>
</div>

<style>
	.preview-container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: #f5f7fa;
	}
	
	.preview-header {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
		text-align: center;
	}
	
	.preview-header h1 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 2rem;
	}
	
	.preview-header p {
		margin: 0 0 1.5rem 0;
		color: #666;
		font-size: 1.1rem;
	}
	
	.back-btn {
		padding: 0.75rem 2rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 10px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.back-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
	}
	
	.preview-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
		gap: 2rem;
		margin-bottom: 2rem;
	}
	
	.preview-section {
		background: white;
		border-radius: 20px;
		padding: 1.5rem;
		box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
	}
	
	.preview-section h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.1rem;
		font-weight: 600;
		padding-bottom: 0.75rem;
		border-bottom: 2px solid #f0f0f0;
	}
	
	.preview-wrapper {
		min-height: 250px;
		border-radius: 15px;
		overflow: hidden;
	}
	
	.gradient-bg {
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		padding: 1rem;
	}
	
	.purple-gradient-bg {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 1rem;
	}
	
	.preview-footer {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
	}
	
	.preview-footer h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.5rem;
	}
	
	.preview-footer ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 0.75rem;
	}
	
	.preview-footer li {
		padding: 0.5rem;
		color: #555;
		font-size: 1rem;
	}
	
	@media (max-width: 768px) {
		.preview-container {
			padding: 1rem;
		}
		
		.preview-grid {
			grid-template-columns: 1fr;
		}
		
		.preview-section {
			padding: 1rem;
		}
		
		.preview-footer ul {
			grid-template-columns: 1fr;
		}
	}
</style>
