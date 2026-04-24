<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	export let points = [];
	export let lineColor = '#4f46e5';

	function buildPath(dataPoints) {
		if (!dataPoints || dataPoints.length === 0) return '';

		const values = dataPoints.map((point) => point.value);
		const min = Math.min(...values);
		const max = Math.max(...values);
		const range = max - min || 1;

		return dataPoints
			.map((point, index) => {
				const x = dataPoints.length === 1 ? 0 : (index / (dataPoints.length - 1)) * 100;
				const y = 100 - ((point.value - min) / range) * 100;
				return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
			})
			.join(' ');
	}

	$: chartPoints = (points || []).map((point) => ({
		label: new Date(point.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
		value: point.avg_score
	}));
	$: linePath = buildPath(chartPoints);
</script>

<div class="trend-chart-shell">
	{#if chartPoints.length > 1}
		<svg viewBox="0 0 100 100" preserveAspectRatio="none" class="trend-chart" aria-hidden="true">
			<defs>
				<linearGradient id="trend-fill" x1="0" x2="0" y1="0" y2="1">
					<stop offset="0%" stop-color={lineColor} stop-opacity="0.22" />
					<stop offset="100%" stop-color={lineColor} stop-opacity="0.02" />
				</linearGradient>
			</defs>
			<path d={linePath} fill="none" stroke={lineColor} stroke-width="2.2" vector-effect="non-scaling-stroke" />
		</svg>
		<div class="trend-labels">
			<span>{chartPoints[0].label}</span>
			<span>{chartPoints[chartPoints.length - 1].label}</span>
		</div>
	{:else}
		<p class="trend-empty">{uiText("Complete more sessions to reveal your trend.", $activeLocale)}</p>
	{/if}
</div>

<style>
	.trend-chart-shell {
		display: grid;
		gap: 0.6rem;
	}

	.trend-chart {
		width: 100%;
		height: 180px;
		overflow: visible;
	}

	.trend-labels {
		display: flex;
		justify-content: space-between;
		font-size: 0.78rem;
		font-weight: 700;
		color: #64748b;
	}

	.trend-empty {
		margin: 0;
		color: #64748b;
		font-size: 0.92rem;
	}
</style>