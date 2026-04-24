<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
</script>

<div class="preview-container">
	<div class="preview-header">
		<h1>{uiText("🎨 Phase 6: Empty States Preview", $activeLocale)}</h1>
		<p>{uiText("All empty states and loading skeletons without clearing your data", $activeLocale)}</p>
		<button class="back-btn" on:click={() => goto('/dashboard')}>{uiText("← Back to Dashboard", $activeLocale)}</button>
	</div>
	
	<div class="preview-grid">
		<!-- Progress Page Empty State -->
		<div class="preview-section">
			<h3>{uiText("Progress Page - No Data", $activeLocale)}</h3>
			<div class="preview-wrapper gradient-bg">
				<EmptyState 
					icon="📊"
					title={uiText("Start Your Progress Journey", $activeLocale)}
					message={uiText("Complete your first training session to see detailed analytics, trends, and badges!", $activeLocale)}
					actionText={uiText("Begin Training", $activeLocale)}
					actionLink="/training"
					tip={uiText("Consistent training leads to measurable cognitive improvements", $activeLocale)}
					variant="large"
				/>
			</div>
		</div>
		
		<!-- Session Summary Empty State -->
		<div class="preview-section">
			<h3>{uiText("Session Summary - No Session", $activeLocale)}</h3>
			<div class="preview-wrapper purple-gradient-bg">
				<EmptyState 
					icon="🎯"
					title={uiText("No Session Data", $activeLocale)}
					message={uiText("Complete a training session to see your celebration summary here!", $activeLocale)}
					actionText={uiText("Start Training", $activeLocale)}
					actionLink="/training"
					tip={uiText("Each session includes 4 cognitive tasks designed to challenge your brain", $activeLocale)}
				/>
			</div>
		</div>
		
		<!-- Weekly Summary Empty State -->
		<div class="preview-section">
			<h3>{uiText("Weekly Summary - Less than 7 Days", $activeLocale)}</h3>
			<div class="preview-wrapper">
				<EmptyState 
					icon="📅"
					title={uiText("Build Your Weekly Streak", $activeLocale)}
					message={uiText("Train for 7 days to unlock your weekly summary with insights and progress tracking!", $activeLocale)}
					actionText={uiText("Start Training", $activeLocale)}
					actionLink="/training"
					tip={uiText("Training multiple days per week shows better cognitive improvements", $activeLocale)}
					variant="compact"
				/>
			</div>
		</div>
		
		<!-- Badges Empty State -->
		<div class="preview-section">
			<h3>{uiText("Badges - No Badges Earned", $activeLocale)}</h3>
			<div class="preview-wrapper">
				<EmptyState 
					icon="🎯"
					title={uiText("Start Earning Badges!", $activeLocale)}
					message={uiText("Complete training sessions to unlock your first achievement badge!", $activeLocale)}
					actionText={uiText("Start Training", $activeLocale)}
					actionLink="/training"
					tip={uiText("Badges track your progress, consistency, and mastery across all cognitive domains", $activeLocale)}
					variant="compact"
				/>
			</div>
		</div>
		
		<!-- Performance Trends Empty State -->
		<div class="preview-section">
			<h3>{uiText("Performance Trends - Not Enough Data", $activeLocale)}</h3>
			<div class="preview-wrapper">
				<EmptyState 
					icon="📈"
					title={uiText("Track Your Progress", $activeLocale)}
					message={uiText("Complete multiple training sessions to unlock your performance trends graph and see how you improve over time!", $activeLocale)}
					actionText={uiText("Start Training", $activeLocale)}
					actionLink="/training"
					tip={uiText("Trends become visible after 3+ sessions", $activeLocale)}
					variant="compact"
				/>
			</div>
		</div>
		
		<!-- Loading Skeleton - Card Variant -->
		<div class="preview-section">
			<h3>{uiText("Loading Skeleton - Card Grid", $activeLocale)}</h3>
			<div class="preview-wrapper">
				<LoadingSkeleton variant="card" count={4} />
			</div>
		</div>
		
		<!-- Loading Skeleton - List Variant -->
		<div class="preview-section">
			<h3>{uiText("Loading Skeleton - List Items", $activeLocale)}</h3>
			<div class="preview-wrapper">
				<LoadingSkeleton variant="list" count={3} />
			</div>
		</div>
		
		<!-- Loading Skeleton - Default Variant -->
		<div class="preview-section">
			<h3>{uiText("Loading Skeleton - Block", $activeLocale)}</h3>
			<div class="preview-wrapper">
				<LoadingSkeleton variant="default" count={2} />
			</div>
		</div>
	</div>
	
	<div class="preview-footer">
		<h3>{uiText("✅ Phase 6 Features Demonstrated:", $activeLocale)}</h3>
		<ul>
			<li>{uiText("✨ Animated icons with bounce effect", $activeLocale)}</li>
			<li>{uiText("🎨 Gradient backgrounds (3 variants: default, compact, large)", $activeLocale)}</li>
			<li>{uiText("💡 Glass-morphism tip cards", $activeLocale)}</li>
			<li>{uiText("🔘 Interactive call-to-action buttons with hover effects", $activeLocale)}</li>
			<li>{uiText("⚡ Shimmer loading skeletons (3 variants: card, list, block)", $activeLocale)}</li>
			<li>{uiText("📱 Fully responsive design", $activeLocale)}</li>
			<li>{uiText("🎯 Context-specific messaging for each empty state", $activeLocale)}</li>
			<li>{uiText("✨ Professional polish throughout", $activeLocale)}</li>
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
