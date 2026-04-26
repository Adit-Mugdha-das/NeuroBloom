<script>
	import { formatDate, formatNumber, locale as activeLocale, uiText } from '$lib/i18n';
	import { downloadCanvasAsPNG, downloadCSV } from '$lib/utils/chartDownload';
	import { onMount } from 'svelte';
	import EmptyState from './EmptyState.svelte';
	
	/** @type {any} */
	export let trendsData = null;
	
	let chartCanvas;
	let chart = null;
	let selectedMetric = 'score';
	let selectedDomain = 'all';
	const metricSelectId = 'performance-trends-metric';
	const domainSelectId = 'performance-trends-domain';
	
	const metricOptions = {
		score: { label: 'Score', color: '#0e7490', unit: '%' },
		accuracy: { label: 'Accuracy', color: '#059669', unit: '%' },
		difficulty: { label: 'Difficulty', color: '#d97706', unit: '' }
	};
	
	const domainNames = {
		working_memory: 'Working Memory',
		attention: 'Attention',
		flexibility: 'Cognitive Flexibility',
		planning: 'Planning',
		processing_speed: 'Processing Speed',
		visual_scanning: 'Visual Scanning'
	};

	function n(value, options = {}) {
		return formatNumber(value, $activeLocale, options);
	}

	function oneDecimal(value) {
		return n(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function shortDate(value) {
		return formatDate(value, $activeLocale, { month: 'short', day: 'numeric' });
	}

	$: availableDomains = Object.keys(trendsData?.trends_by_domain || {});
	$: hasTrendSessions = (trendsData?.total_sessions || 0) > 0;
	
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
			const overallTrend = trendsData.overall_trend || [];
			const data = overallTrend.map(point => ({
				x: shortDate(point.date),
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
			const domainData = trendsData.trends_by_domain?.[selectedDomain];
			if (domainData) {
			const dataPoints = domainData.data_points || [];
			const data = dataPoints.map(point => ({
					x: shortDate(point.date),
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
			ctx.fillText(uiText('No data available', $activeLocale), width / 2, height / 2);
			return { destroy: () => {} };
		}
		
		const data = datasets[0].data;
		const values = data.map(d => d.y);
		const minValue = Math.min(...values);
		const maxValue = Math.max(...values);
		const range = maxValue - minValue || 1;
		
		const chartWidth = width - padding.left - padding.right;
		const chartHeight = height - padding.top - padding.bottom;
		
		// Draw background
		ctx.fillStyle = '#ffffff';
		ctx.fillRect(0, 0, width, height);

		// Draw grid lines
		const gridCount = 5;
		for (let i = 0; i <= gridCount; i++) {
			const y = padding.top + (chartHeight / gridCount) * i;
			ctx.strokeStyle = i === gridCount ? '#d1e9f0' : '#e8f4f8';
			ctx.lineWidth = i === gridCount ? 1.5 : 1;
			ctx.beginPath();
			ctx.moveTo(padding.left, y);
			ctx.lineTo(width - padding.right, y);
			ctx.stroke();

			// Y-axis labels
			const value = maxValue - (range / gridCount) * i;
			ctx.fillStyle = '#94a3b8';
			ctx.font = '600 11px Inter, system-ui, sans-serif';
			ctx.textAlign = 'right';
			ctx.fillText(oneDecimal(value), padding.left - 8, y + 4);
		}

		// Compute smoothed points using cardinal spline
		const pts = data.map((point, i) => ({
			x: padding.left + (chartWidth / (data.length - 1 || 1)) * i,
			y: padding.top + chartHeight - ((point.y - minValue) / range) * chartHeight
		}));

		// Draw filled area first (gradient)
		const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
		grad.addColorStop(0, datasets[0].borderColor + '30');
		grad.addColorStop(1, datasets[0].borderColor + '05');
		ctx.fillStyle = grad;
		ctx.beginPath();
		ctx.moveTo(pts[0].x, pts[0].y);
		if (pts.length === 1) {
			ctx.lineTo(pts[0].x, pts[0].y);
		} else {
			for (let i = 0; i < pts.length - 1; i++) {
				const cpx = (pts[i].x + pts[i + 1].x) / 2;
				ctx.bezierCurveTo(cpx, pts[i].y, cpx, pts[i + 1].y, pts[i + 1].x, pts[i + 1].y);
			}
		}
		ctx.lineTo(pts[pts.length - 1].x, padding.top + chartHeight);
		ctx.lineTo(pts[0].x, padding.top + chartHeight);
		ctx.closePath();
		ctx.fill();

		// Draw smooth line
		ctx.strokeStyle = datasets[0].borderColor;
		ctx.lineWidth = 2.5;
		ctx.lineJoin = 'round';
		ctx.beginPath();
		ctx.moveTo(pts[0].x, pts[0].y);
		if (pts.length === 1) {
			ctx.lineTo(pts[0].x, pts[0].y);
		} else {
			for (let i = 0; i < pts.length - 1; i++) {
				const cpx = (pts[i].x + pts[i + 1].x) / 2;
				ctx.bezierCurveTo(cpx, pts[i].y, cpx, pts[i + 1].y, pts[i + 1].x, pts[i + 1].y);
			}
		}
		ctx.stroke();

		// Draw points
		pts.forEach(pt => {
			// outer white ring
			ctx.beginPath();
			ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
			ctx.fillStyle = '#ffffff';
			ctx.fill();
			// inner colored dot
			ctx.beginPath();
			ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
			ctx.fillStyle = datasets[0].borderColor;
			ctx.fill();
		});

		// X-axis labels
		ctx.fillStyle = '#94a3b8';
		ctx.font = '600 11px Inter, system-ui, sans-serif';
		ctx.textAlign = 'center';
		const labelStep = Math.ceil(data.length / 8);
		data.forEach((point, i) => {
			if (i % labelStep === 0 || i === data.length - 1) {
				ctx.fillText(point.x, pts[i].x, height - 10);
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
	
	function handleDownloadChart() {
		if (!chartCanvas) return;
		const filename = `performance-trends-${selectedDomain}-${selectedMetric}-${new Date().toISOString().split('T')[0]}`;
		downloadCanvasAsPNG(chartCanvas, filename);
	}
	
	function handleDownloadData() {
		if (!trendsData) return;
		
		let data = [];
		if (selectedDomain === 'all') {
			data = (trendsData.overall_trend || []).map(point => ({
				date: point.date,
				score: point.avg_score,
				accuracy: point.avg_accuracy,
				difficulty: point.avg_difficulty
			}));
		} else {
			const domainData = trendsData.trends_by_domain?.[selectedDomain];
			if (domainData) {
				data = (domainData.data_points || []).map(point => ({
					date: point.date,
					domain: selectedDomain,
					score: point.score,
					accuracy: point.accuracy,
					difficulty: point.difficulty
				}));
			}
		}
		
		const filename = `performance-data-${selectedDomain}-${new Date().toISOString().split('T')[0]}`;
		downloadCSV(data, filename);
	}
</script>

<div class="trends-card">
	<div class="trends-header">
		<div class="header-left">
			<h3>Performance Trends</h3>
			<p class="subtitle">{uiText("Track your progress over time", $activeLocale)}</p>
		</div>

		<div class="header-right">
			{#if hasTrendSessions}
				<div class="download-group">
					<button class="download-btn" on:click={handleDownloadChart} title={uiText("Download chart as image", $activeLocale)}>
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
						{uiText("Chart", $activeLocale)}
					</button>
					<button class="download-btn" on:click={handleDownloadData} title={uiText("Download data as CSV", $activeLocale)}>
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
						{uiText("Data", $activeLocale)}
					</button>
				</div>
			{/if}

			<div class="controls">
				<div class="selector">
					<label for={metricSelectId}>{uiText("Metric:", $activeLocale)}</label>
					<select id={metricSelectId} bind:value={selectedMetric} on:change={updateChart}>
						<option value="score">{uiText("Score", $activeLocale)}</option>
						<option value="accuracy">{uiText("Accuracy", $activeLocale)}</option>
						<option value="difficulty">{uiText("Difficulty", $activeLocale)}</option>
					</select>
				</div>
				<div class="selector">
					<label for={domainSelectId}>{uiText("Domain:", $activeLocale)}</label>
					<select id={domainSelectId} bind:value={selectedDomain} on:change={updateChart}>
						<option value="all">{uiText("Overall", $activeLocale)}</option>
						{#if availableDomains.length > 0}
							{#each availableDomains as domain}
								<option value={domain}>{uiText(domainNames[domain], $activeLocale)}</option>
							{/each}
						{/if}
					</select>
				</div>
			</div>
		</div>
	</div>
	
	<div class="chart-container">
		{#if hasTrendSessions}
			<canvas bind:this={chartCanvas} width="900" height="320"></canvas>
		{:else}
			<EmptyState 
				icon="📈"
				title={uiText("Track Your Progress", $activeLocale)}
				message={uiText("Complete multiple training sessions to unlock your performance trends graph and see how you improve over time!", $activeLocale)}
				actionText={uiText("Start Training", $activeLocale)}
				actionLink="/training"
				tip={uiText("Trends become visible after 3+ training sessions", $activeLocale)}
				variant="compact"
			/>
		{/if}
	</div>
	
	{#if hasTrendSessions}
		<div class="stats-summary">
			<div class="stat-item">
				<span class="stat-label">{uiText("Total Sessions", $activeLocale)}</span>
				<span class="stat-value">{n(trendsData.total_sessions)}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">{uiText("Period", $activeLocale)}</span>
				<span class="stat-value">{n(trendsData.period_days)} {uiText("days", $activeLocale)}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">{uiText("Active Domains", $activeLocale)}</span>
				<span class="stat-value">{n(availableDomains.length)}</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.trends-card {
		background: #ffffff;
		border-radius: 16px;
		padding: 1.75rem 2rem;
		border: 1px solid #e2eef3;
		box-shadow: 0 2px 12px rgba(14, 116, 144, 0.07);
		margin-bottom: 2rem;
	}

	.trends-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.25rem;
		gap: 1.5rem;
		flex-wrap: wrap;
	}

	.header-left h3 {
		margin: 0 0 0.2rem 0;
		color: #0f172a;
		font-size: 1.15rem;
		font-weight: 700;
		letter-spacing: -0.01em;
	}

	.subtitle {
		margin: 0;
		color: #64748b;
		font-size: 0.82rem;
	}

	.header-right {
		display: flex;
		align-items: flex-end;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.download-group {
		display: flex;
		gap: 0.4rem;
		align-items: flex-end;
	}

	.download-btn {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.42rem 0.85rem;
		background: #f0f9ff;
		color: #0e7490;
		border: 1.5px solid #bae6fd;
		border-radius: 8px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s, border-color 0.15s, color 0.15s;
	}

	.download-btn:hover {
		background: #e0f2fe;
		border-color: #0e7490;
		color: #164e63;
	}

	.download-btn:active {
		background: #bae6fd;
	}

	.controls {
		display: flex;
		gap: 0.75rem;
		align-items: flex-end;
	}

	.selector {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.selector label {
		font-size: 0.75rem;
		color: #64748b;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.selector select {
		padding: 0.42rem 2rem 0.42rem 0.75rem;
		border: 1.5px solid #cbd5e1;
		border-radius: 8px;
		background: #ffffff;
		color: #0f172a;
		font-size: 0.875rem;
		cursor: pointer;
		transition: border-color 0.15s, box-shadow 0.15s;
		appearance: none;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 0.6rem center;
	}

	.selector select:hover {
		border-color: #0e7490;
	}

	.selector select:focus {
		outline: none;
		border-color: #0e7490;
		box-shadow: 0 0 0 3px rgba(14, 116, 144, 0.1);
	}

	.chart-container {
		background: #ffffff;
		border: 1px solid #e8f4f8;
		border-radius: 12px;
		padding: 1rem 0.5rem 0.5rem 0.5rem;
		min-height: 280px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	canvas {
		max-width: 100%;
		height: auto;
		display: block;
	}

	.stats-summary {
		display: flex;
		justify-content: center;
		gap: 0;
		margin-top: 1.25rem;
		padding-top: 1.25rem;
		border-top: 1px solid #f1f5f9;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		flex: 1;
		padding: 0 1rem;
	}

	.stat-item + .stat-item {
		border-left: 1px solid #e2e8f0;
	}

	.stat-label {
		font-size: 0.75rem;
		color: #94a3b8;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.stat-value {
		font-size: 1.5rem;
		color: #0e7490;
		font-weight: 700;
		line-height: 1;
	}

	@media (max-width: 768px) {
		.trends-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.header-right {
			width: 100%;
			flex-direction: column;
			align-items: flex-start;
		}

		.controls {
			width: 100%;
		}

		.selector {
			flex: 1;
			min-width: 130px;
		}

		.chart-container {
			padding: 0.5rem;
		}

		.stats-summary {
			flex-wrap: wrap;
			gap: 1rem;
		}
	}
</style>
