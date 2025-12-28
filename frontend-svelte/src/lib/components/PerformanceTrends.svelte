<script>
	import { onMount } from 'svelte';
	
	/** @type {any} */
	export let trendsData = null;
	
	let chartCanvas;
	let chart = null;
	let selectedMetric = 'score';
	let selectedDomain = 'all';
	
	const metricOptions = {
		score: { label: 'Score', color: '#667eea', unit: '%' },
		accuracy: { label: 'Accuracy', color: '#4caf50', unit: '%' },
		difficulty: { label: 'Difficulty', color: '#ff9800', unit: '' }
	};
	
	const domainNames = {
		working_memory: 'Working Memory',
		attention: 'Attention',
		flexibility: 'Cognitive Flexibility',
		planning: 'Planning',
		processing_speed: 'Processing Speed',
		visual_scanning: 'Visual Scanning'
	};
	
	$: if (trendsData && chartCanvas) {
		updateChart();
	}
	
	function updateChart() {
		if (!trendsData || !chartCanvas) return;
		
		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}
		
		const ctx = chartCanvas.getContext('2d');
		
		let datasets = [];
		
		if (selectedDomain === 'all') {
			// Show overall trend
			const data = trendsData.overall_trend.map(point => ({
				x: point.date,
				y: selectedMetric === 'score' ? point.avg_score :
				   selectedMetric === 'accuracy' ? point.avg_accuracy :
				   point.avg_difficulty
			}));
			
			datasets.push({
				label: `Overall ${metricOptions[selectedMetric].label}`,
				data: data,
				borderColor: metricOptions[selectedMetric].color,
				backgroundColor: metricOptions[selectedMetric].color + '20',
				fill: true,
				tension: 0.4,
				pointRadius: 4,
				pointHoverRadius: 6
			});
		} else {
			// Show specific domain
			const domainData = trendsData.trends_by_domain[selectedDomain];
			if (domainData) {
				const data = domainData.data_points.map(point => ({
					x: new Date(point.date).toLocaleDateString(),
					y: selectedMetric === 'score' ? point.score :
					   selectedMetric === 'accuracy' ? point.accuracy :
					   point.difficulty
				}));
				
				datasets.push({
					label: `${domainNames[selectedDomain]} - ${metricOptions[selectedMetric].label}`,
					data: data,
					borderColor: metricOptions[selectedMetric].color,
					backgroundColor: metricOptions[selectedMetric].color + '20',
					fill: true,
					tension: 0.4,
					pointRadius: 4,
					pointHoverRadius: 6
				});
			}
		}
		
		// Create chart using vanilla JS (Chart.js style API)
		chart = createSimpleChart(ctx, datasets);
	}
	
	function createSimpleChart(ctx, datasets) {
		// Simple canvas-based chart (no external library needed)
		const canvas = ctx.canvas;
		const width = canvas.width;
		const height = canvas.height;
		const padding = { top: 20, right: 20, bottom: 40, left: 60 };
		
		// Clear canvas
		ctx.clearRect(0, 0, width, height);
		
		if (!datasets[0] || datasets[0].data.length === 0) {
			ctx.fillStyle = '#999';
			ctx.font = '14px sans-serif';
			ctx.textAlign = 'center';
			ctx.fillText('No data available', width / 2, height / 2);
			return { destroy: () => {} };
		}
		
		const data = datasets[0].data;
		const values = data.map(d => d.y);
		const minValue = Math.min(...values);
		const maxValue = Math.max(...values);
		const range = maxValue - minValue || 1;
		
		const chartWidth = width - padding.left - padding.right;
		const chartHeight = height - padding.top - padding.bottom;
		
		// Draw grid
		ctx.strokeStyle = '#f0f0f0';
		ctx.lineWidth = 1;
		for (let i = 0; i <= 5; i++) {
			const y = padding.top + (chartHeight / 5) * i;
			ctx.beginPath();
			ctx.moveTo(padding.left, y);
			ctx.lineTo(width - padding.right, y);
			ctx.stroke();
			
			// Y-axis labels
			const value = maxValue - (range / 5) * i;
			ctx.fillStyle = '#666';
			ctx.font = '12px sans-serif';
			ctx.textAlign = 'right';
			ctx.fillText(value.toFixed(1), padding.left - 10, y + 4);
		}
		
		// Draw line
		ctx.strokeStyle = datasets[0].borderColor;
		ctx.fillStyle = datasets[0].backgroundColor;
		ctx.lineWidth = 2;
		
		ctx.beginPath();
		data.forEach((point, i) => {
			const x = padding.left + (chartWidth / (data.length - 1 || 1)) * i;
			const y = padding.top + chartHeight - ((point.y - minValue) / range) * chartHeight;
			
			if (i === 0) {
				ctx.moveTo(x, y);
			} else {
				ctx.lineTo(x, y);
			}
		});
		ctx.stroke();
		
		// Fill area
		ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
		ctx.lineTo(padding.left, padding.top + chartHeight);
		ctx.closePath();
		ctx.fill();
		
		// Draw points
		ctx.fillStyle = datasets[0].borderColor;
		data.forEach((point, i) => {
			const x = padding.left + (chartWidth / (data.length - 1 || 1)) * i;
			const y = padding.top + chartHeight - ((point.y - minValue) / range) * chartHeight;
			
			ctx.beginPath();
			ctx.arc(x, y, 4, 0, Math.PI * 2);
			ctx.fill();
		});
		
		// X-axis labels (show every nth label to avoid crowding)
		ctx.fillStyle = '#666';
		ctx.font = '11px sans-serif';
		ctx.textAlign = 'center';
		const labelStep = Math.ceil(data.length / 8);
		data.forEach((point, i) => {
			if (i % labelStep === 0 || i === data.length - 1) {
				const x = padding.left + (chartWidth / (data.length - 1 || 1)) * i;
				ctx.fillText(point.x, x, height - 15);
			}
		});
		
		return {
			destroy: () => ctx.clearRect(0, 0, width, height)
		};
	}
	
	onMount(() => {
		if (trendsData) {
			updateChart();
		}
	});
</script>

<div class="trends-card">
	<div class="trends-header">
		<div class="header-left">
			<h3>📈 Performance Trends</h3>
			<p class="subtitle">Track your progress over time</p>
		</div>
		
		<div class="controls">
			<!-- Metric Selector -->
			<div class="selector">
				<label>Metric:</label>
				<select bind:value={selectedMetric} on:change={updateChart}>
					<option value="score">Score</option>
					<option value="accuracy">Accuracy</option>
					<option value="difficulty">Difficulty</option>
				</select>
			</div>
			
			<!-- Domain Selector -->
			<div class="selector">
				<label>Domain:</label>
				<select bind:value={selectedDomain} on:change={updateChart}>
					<option value="all">Overall</option>
					{#if trendsData}
						{#each trendsData.domains as domain}
							<option value={domain}>{domainNames[domain]}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>
	</div>
	
	<div class="chart-container">
		{#if trendsData && trendsData.total_sessions > 0}
			<canvas bind:this={chartCanvas} width="800" height="300"></canvas>
		{:else}
			<div class="empty-state">
				<div class="empty-icon">📊</div>
				<p>No training data yet</p>
				<small>Complete some sessions to see your progress trends</small>
			</div>
		{/if}
	</div>
	
	{#if trendsData && trendsData.total_sessions > 0}
		<div class="stats-summary">
			<div class="stat-item">
				<span class="stat-label">Total Sessions</span>
				<span class="stat-value">{trendsData.total_sessions}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">Period</span>
				<span class="stat-value">{trendsData.period_days} days</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">Active Domains</span>
				<span class="stat-value">{trendsData.domains.length}</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.trends-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		margin-bottom: 2rem;
	}
	
	.trends-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 2rem;
		gap: 2rem;
	}
	
	.header-left h3 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 1.5rem;
	}
	
	.subtitle {
		margin: 0;
		color: #666;
		font-size: 0.9rem;
	}
	
	.controls {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.selector {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.selector label {
		font-size: 0.85rem;
		color: #666;
		font-weight: 600;
	}
	
	.selector select {
		padding: 0.5rem 1rem;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		background: white;
		color: #333;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.selector select:hover {
		border-color: #667eea;
	}
	
	.selector select:focus {
		outline: none;
		border-color: #667eea;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}
	
	.chart-container {
		background: #f8f9fa;
		border-radius: 15px;
		padding: 2rem;
		min-height: 300px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	canvas {
		max-width: 100%;
		height: auto;
	}
	
	.empty-state {
		text-align: center;
		padding: 3rem 2rem;
		color: #999;
	}
	
	.empty-icon {
		font-size: 4rem;
		margin-bottom: 1rem;
		opacity: 0.5;
	}
	
	.empty-state p {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #666;
	}
	
	.empty-state small {
		font-size: 0.9rem;
	}
	
	.stats-summary {
		display: flex;
		justify-content: space-around;
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 2px solid #f0f0f0;
	}
	
	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.stat-label {
		font-size: 0.85rem;
		color: #666;
		font-weight: 600;
	}
	
	.stat-value {
		font-size: 1.5rem;
		color: #667eea;
		font-weight: 700;
	}
	
	@media (max-width: 768px) {
		.trends-header {
			flex-direction: column;
		}
		
		.controls {
			width: 100%;
		}
		
		.selector {
			flex: 1;
			min-width: 140px;
		}
		
		.chart-container {
			padding: 1rem;
		}
		
		.stats-summary {
			flex-wrap: wrap;
			gap: 1.5rem;
		}
	}
</style>
