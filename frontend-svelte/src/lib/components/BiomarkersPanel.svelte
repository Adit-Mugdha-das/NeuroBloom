<script>
	/**
	 * BiomarkersPanel.svelte
	 * Displays MS digital biomarkers extracted from cognitive training data.
	 *
	 * Props:
	 *   biomarkerData  - response from GET /api/training/advanced-analytics/{id}/biomarkers
	 *   doctorView     - true = full clinical labels; false = patient-friendly language
	 *   days           - period used (shown in header)
	 */

	/** @type {any} */
	export let biomarkerData = null;
	export let doctorView = false;
	export let days = 30;

	// ── Fatigue ──────────────────────────────────────────────
	function getFatigueLevel(index) {
		if (index === null || index === undefined) return null;
		if (index > 0.5)  return { label: 'High',     color: '#f44336', bg: '#ffebee', pct: Math.min(100, index * 100) };
		if (index > 0.3)  return { label: 'Moderate', color: '#ff9800', bg: '#fff3e0', pct: Math.min(100, index * 100) };
		return              { label: 'Low',      color: '#4caf50', bg: '#e8f5e9', pct: Math.min(100, index * 100) };
	}

	// ── CV ───────────────────────────────────────────────────
	function getCVLevel(cv) {
		if (cv === null || cv === undefined) return null;
		if (cv > 0.35)  return { label: 'High variability',      color: '#f44336', bg: '#ffebee', pct: Math.min(100, cv * 200) };
		if (cv > 0.25)  return { label: 'Moderate variability',  color: '#ff9800', bg: '#fff3e0', pct: Math.min(100, cv * 200) };
		return           { label: 'Normal consistency',          color: '#4caf50', bg: '#e8f5e9', pct: Math.min(100, cv * 200) };
	}

	// ── RCI ──────────────────────────────────────────────────
	function getRCIInfo(rci) {
		if (rci === null || rci === undefined) return null;
		if (rci > 1.96)  return { label: 'Significant improvement', icon: '📈', color: '#4caf50', bg: '#e8f5e9' };
		if (rci < -1.96) return { label: 'Significant decline',     icon: '📉', color: '#f44336', bg: '#ffebee' };
		return            { label: 'Stable — no significant change', icon: '➡️', color: '#667eea', bg: '#f0f2ff' };
	}

	// ── Trend ────────────────────────────────────────────────
	function getTrendInfo(direction, strength) {
		const d = (direction || '').toLowerCase();
		if (d === 'improving') return { icon: '↗', label: 'Improving', color: '#4caf50', bg: '#e8f5e9' };
		if (d === 'declining') return { icon: '↘', label: 'Declining', color: '#f44336', bg: '#ffebee' };
		return                  { icon: '→', label: 'Stable',    color: '#667eea', bg: '#f0f2ff' };
	}

	// ── Correlations ─────────────────────────────────────────
	function corrBar(r) {
		// Returns a 0-100 width for the bar (|r| mapped to 0-100)
		return Math.min(100, Math.abs(r || 0) * 100);
	}

	function corrColor(r) {
		const abs = Math.abs(r || 0);
		if (abs >= 0.6) return '#f44336';
		if (abs >= 0.3) return '#ff9800';
		return '#4caf50';
	}

	function corrLabel(r, factor) {
		if (!r) return 'Not enough data';
		const strength = Math.abs(r) >= 0.6 ? 'Strong' : Math.abs(r) >= 0.3 ? 'Moderate' : 'Weak';
		const direction = r < 0 ? 'negative' : 'positive';
		return `${strength} ${direction} effect`;
	}

	// ── Patient-friendly aliases ──────────────────────────────
	function fatigueTitle() {
		return doctorView ? 'Fatigue Index' : 'Brain Fatigue Level';
	}
	function cvTitle() {
		return doctorView ? 'Coefficient of Variation (CV)' : 'Response Consistency';
	}
	function rciTitle() {
		return doctorView ? 'Reliable Change Index (RCI)' : 'Performance Change';
	}
	function trendTitle() {
		return doctorView ? 'EWMA Trend Analysis' : 'Overall Trend';
	}

	// Derived values (reactive)
	$: fatigue    = biomarkerData?.fatigue_index?.mean ?? null;
	$: fatigueInterp = biomarkerData?.fatigue_index?.interpretation ?? null;
	$: cv         = biomarkerData?.rt_coefficient_of_variation?.mean ?? null;
	$: rciVal     = biomarkerData?.reliable_change_index?.value ?? null;
	$: rciInterp  = biomarkerData?.reliable_change_index?.interpretation ?? null;
	$: trend      = biomarkerData?.performance_trend ?? null;
	$: rtTrend    = biomarkerData?.rt_trend ?? null;
	$: fatCorr    = biomarkerData?.fatigue_correlation ?? null;
	$: sleepCorr  = biomarkerData?.sleep_correlation ?? null;
	$: medCorr    = biomarkerData?.medication_timing_correlation ?? null;
	$: totalSessions = biomarkerData?.total_sessions ?? 0;

	$: fatigueInfo = getFatigueLevel(fatigue);
	$: cvInfo      = getCVLevel(cv);
	$: rciInfo     = getRCIInfo(rciVal);
	$: trendInfo   = trend ? getTrendInfo(trend.direction, trend.strength) : null;
	$: rtTrendInfo = rtTrend ? getTrendInfo(rtTrend.direction, rtTrend.strength) : null;

	$: hasData = biomarkerData && totalSessions >= 3;
</script>

<div class="biomarkers-panel">
	<!-- Header -->
	<div class="panel-header">
		<div class="header-left">
			<h3>🧬 {doctorView ? 'MS Digital Biomarkers' : 'Brain Health Indicators'}</h3>
			<p class="subtitle">
				{doctorView
					? `Clinical metrics extracted from ${totalSessions} sessions · Last ${days} days`
					: `Based on your last ${days} days of training · ${totalSessions} sessions`}
			</p>
		</div>
		{#if doctorView}
			<div class="research-badge">Research Grade</div>
		{/if}
	</div>

	{#if !hasData}
		<div class="no-data-state">
			<div class="no-data-icon">🧠</div>
			<p class="no-data-title">
				{totalSessions < 3
					? `${3 - totalSessions} more session${3 - totalSessions === 1 ? '' : 's'} needed`
					: 'No data available yet'}
			</p>
			<p class="no-data-sub">
				{doctorView
					? 'Complete at least 3 training sessions to generate MS biomarkers.'
					: 'Keep training! Brain health indicators unlock after 3 sessions.'}
			</p>
		</div>
	{:else}
		<!-- Top row: 3 metric cards -->
		<div class="metrics-grid">

			<!-- 1. Fatigue Index -->
			<div class="metric-card" style="--card-bg: {fatigueInfo?.bg ?? '#f5f5f5'}">
				<div class="metric-header">
					<span class="metric-icon">⚡</span>
					<span class="metric-title">{fatigueTitle()}</span>
				</div>
				<div class="metric-value" style="color: {fatigueInfo?.color ?? '#666'}">
					{fatigue !== null ? fatigue.toFixed(2) : '—'}
				</div>
				<div class="metric-bar-wrap">
					<div class="metric-bar">
						<div
							class="metric-bar-fill"
							style="width: {fatigueInfo?.pct ?? 0}%; background: {fatigueInfo?.color ?? '#ccc'}"
						></div>
					</div>
					<span class="bar-labels"><span>None</span><span>Severe</span></span>
				</div>
				<div class="metric-tag" style="color: {fatigueInfo?.color}; background: {fatigueInfo?.bg}">
					{fatigueInfo?.label ?? '—'}
				</div>
				{#if doctorView}
					<p class="metric-note">
						>0.5 = severe fatigue · may indicate relapse or poor disease control
					</p>
				{:else}
					<p class="metric-note">
						{(fatigue ?? 0) > 0.4
							? 'You tend to tire during tasks — rest before training helps'
							: 'Good energy levels maintained throughout tasks'}
					</p>
				{/if}
			</div>

			<!-- 2. CV / Consistency -->
			<div class="metric-card" style="--card-bg: {cvInfo?.bg ?? '#f5f5f5'}">
				<div class="metric-header">
					<span class="metric-icon">🎯</span>
					<span class="metric-title">{cvTitle()}</span>
				</div>
				<div class="metric-value" style="color: {cvInfo?.color ?? '#666'}">
					{cv !== null ? cv.toFixed(3) : '—'}
				</div>
				<div class="metric-bar-wrap">
					<div class="metric-bar">
						<div
							class="metric-bar-fill"
							style="width: {cvInfo?.pct ?? 0}%; background: {cvInfo?.color ?? '#ccc'}"
						></div>
					</div>
					<span class="bar-labels"><span>Consistent</span><span>Erratic</span></span>
				</div>
				<div class="metric-tag" style="color: {cvInfo?.color}; background: {cvInfo?.bg}">
					{cvInfo?.label ?? '—'}
				</div>
				{#if doctorView}
					<p class="metric-note">
						CV >0.35 = clinically significant RT variability · IIV MS biomarker
					</p>
				{:else}
					<p class="metric-note">
						{(cv ?? 0) > 0.3
							? 'Your response times vary quite a bit — this is common in MS'
							: 'Your brain responses are fairly consistent — great sign!'}
					</p>
				{/if}
			</div>

			<!-- 3. RCI -->
			<div class="metric-card" style="--card-bg: {rciInfo?.bg ?? '#f5f5f5'}">
				<div class="metric-header">
					<span class="metric-icon">{rciInfo?.icon ?? '📊'}</span>
					<span class="metric-title">{rciTitle()}</span>
				</div>
				<div class="metric-value" style="color: {rciInfo?.color ?? '#666'}">
					{rciVal !== null ? (rciVal > 0 ? '+' : '') + rciVal.toFixed(2) : '—'}
				</div>
				<div class="rci-scale">
					<div class="rci-track">
						<div class="rci-center-line"></div>
						<div
							class="rci-marker"
							style="left: calc(50% + {Math.min(50, Math.max(-50, (rciVal ?? 0) * 12.75))}%); background: {rciInfo?.color}"
						></div>
					</div>
					<span class="bar-labels"><span>Declining</span><span>Improving</span></span>
				</div>
				<div class="metric-tag" style="color: {rciInfo?.color}; background: {rciInfo?.bg}">
					{rciInfo?.label ?? '—'}
				</div>
				{#if doctorView}
					<p class="metric-note">
						|RCI| >1.96 = statistically significant change (Jacobson & Truax 1991)
					</p>
				{:else}
					<p class="metric-note">
						{rciInterp ?? 'Comparing your current scores to your starting point'}
					</p>
				{/if}
			</div>
		</div>

		<!-- Trend row -->
		<div class="trend-row">
			<!-- Score trend -->
			<div class="trend-card" style="background: {trendInfo?.bg ?? '#f0f2ff'}">
				<div class="trend-icon" style="color: {trendInfo?.color}">
					{trendInfo?.icon ?? '→'}
				</div>
				<div class="trend-body">
					<div class="trend-label">{trendTitle()}</div>
					<div class="trend-value" style="color: {trendInfo?.color}">
						{trendInfo?.label ?? 'Stable'}
						{#if trend?.strength}
							<span class="trend-strength">· {trend.strength}</span>
						{/if}
					</div>
					{#if trend?.current_ewma}
						<div class="trend-ewma">Current EWMA: {trend.current_ewma.toFixed(1)}</div>
					{/if}
				</div>
			</div>

			<!-- RT trend (doctor only) -->
			{#if doctorView && rtTrendInfo}
				<div class="trend-card" style="background: {rtTrendInfo?.bg ?? '#f0f2ff'}">
					<div class="trend-icon" style="color: {rtTrendInfo?.color}">
						{rtTrendInfo?.icon ?? '→'}
					</div>
					<div class="trend-body">
						<div class="trend-label">Reaction Time Trend</div>
						<div class="trend-value" style="color: {rtTrendInfo?.color}">
							{rtTrendInfo?.label ?? 'Stable'}
							{#if rtTrend?.strength}
								<span class="trend-strength">· {rtTrend.strength}</span>
							{/if}
						</div>
						{#if rtTrend?.current_ewma}
							<div class="trend-ewma">Current EWMA: {rtTrend.current_ewma.toFixed(0)} ms</div>
						{/if}
					</div>
				</div>
			{/if}
		</div>

		<!-- Contextual Correlations — doctor view only -->
		{#if doctorView && (fatCorr?.sample_size >= 3 || sleepCorr?.sample_size >= 3 || medCorr?.sample_size >= 3)}
			<div class="correlations-section">
				<h4 class="corr-title">🔗 Contextual Correlations
					<span class="corr-subtitle">(Pearson r — how much each factor affects performance)</span>
				</h4>
				<div class="corr-grid">

					{#if fatCorr?.sample_size >= 3}
						<div class="corr-card">
							<div class="corr-factor">⚡ Fatigue Level</div>
							<div class="corr-row">
								<span class="corr-dim">Score impact</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(fatCorr.correlation_with_score)}%; background: {corrColor(fatCorr.correlation_with_score)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(fatCorr.correlation_with_score)}">
									r = {(fatCorr.correlation_with_score ?? 0).toFixed(2)}
								</span>
							</div>
							<div class="corr-row">
								<span class="corr-dim">RT impact</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(fatCorr.correlation_with_rt)}%; background: {corrColor(fatCorr.correlation_with_rt)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(fatCorr.correlation_with_rt)}">
									r = {(fatCorr.correlation_with_rt ?? 0).toFixed(2)}
								</span>
							</div>
							<div class="corr-interp">{corrLabel(fatCorr.correlation_with_score, 'fatigue')} on score · n={fatCorr.sample_size}</div>
						</div>
					{/if}

					{#if sleepCorr?.sample_size >= 3}
						<div class="corr-card">
							<div class="corr-factor">😴 Sleep Quality</div>
							<div class="corr-row">
								<span class="corr-dim">Score impact</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(sleepCorr.correlation_with_score)}%; background: {corrColor(sleepCorr.correlation_with_score)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(sleepCorr.correlation_with_score)}">
									r = {(sleepCorr.correlation_with_score ?? 0).toFixed(2)}
								</span>
							</div>
							<div class="corr-row">
								<span class="corr-dim">RT impact</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(sleepCorr.correlation_with_rt)}%; background: {corrColor(sleepCorr.correlation_with_rt)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(sleepCorr.correlation_with_rt)}">
									r = {(sleepCorr.correlation_with_rt ?? 0).toFixed(2)}
								</span>
							</div>
							<div class="corr-interp">{corrLabel(sleepCorr.correlation_with_score, 'sleep')} on score · n={sleepCorr.sample_size}</div>
						</div>
					{/if}

					{#if medCorr?.sample_size >= 3}
						<div class="corr-card">
							<div class="corr-factor">💊 Medication Timing</div>
							<div class="corr-row">
								<span class="corr-dim">Score impact</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(medCorr.correlation_with_score)}%; background: {corrColor(medCorr.correlation_with_score)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(medCorr.correlation_with_score)}">
									r = {(medCorr.correlation_with_score ?? 0).toFixed(2)}
								</span>
							</div>
							<div class="corr-row">
								<span class="corr-dim">RT impact</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(medCorr.correlation_with_rt)}%; background: {corrColor(medCorr.correlation_with_rt)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(medCorr.correlation_with_rt)}">
									r = {(medCorr.correlation_with_rt ?? 0).toFixed(2)}
								</span>
							</div>
							<div class="corr-interp">{corrLabel(medCorr.correlation_with_score, 'medication')} on score · n={medCorr.sample_size}</div>
						</div>
					{/if}

				</div>
			</div>
		{/if}

		<!-- Legend for doctor view -->
		{#if doctorView}
			<div class="clinical-legend">
				<span class="legend-item"><span class="dot green"></span> Normal / Improving</span>
				<span class="legend-item"><span class="dot amber"></span> Moderate / Watch</span>
				<span class="legend-item"><span class="dot red"></span> High / Declining</span>
				<span class="legend-sep">|</span>
				<span class="legend-note">Based on BICAMS standards · RCI threshold ±1.96</span>
			</div>
		{/if}
	{/if}
</div>

<style>
	.biomarkers-panel {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
		margin-bottom: 2rem;
	}

	/* ── Header ── */
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.75rem;
		gap: 1rem;
	}

	.header-left h3 {
		margin: 0 0 0.35rem 0;
		font-size: 1.4rem;
		color: #333;
	}

	.subtitle {
		margin: 0;
		font-size: 0.875rem;
		color: #888;
	}

	.research-badge {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		font-size: 0.75rem;
		font-weight: 700;
		padding: 0.35rem 0.85rem;
		border-radius: 20px;
		white-space: nowrap;
		letter-spacing: 0.5px;
	}

	/* ── No-data state ── */
	.no-data-state {
		text-align: center;
		padding: 3rem 2rem;
		color: #aaa;
	}

	.no-data-icon { font-size: 3.5rem; margin-bottom: 1rem; }

	.no-data-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #666;
		margin: 0 0 0.5rem 0;
	}

	.no-data-sub {
		font-size: 0.9rem;
		color: #999;
		margin: 0;
	}

	/* ── Metrics grid ── */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.25rem;
		margin-bottom: 1.25rem;
	}

	.metric-card {
		background: var(--card-bg, #fafafa);
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		border: 1px solid rgba(0,0,0,0.06);
		transition: transform 0.2s;
	}

	.metric-card:hover { transform: translateY(-2px); }

	.metric-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #555;
	}

	.metric-icon { font-size: 1rem; }

	.metric-value {
		font-size: 2rem;
		font-weight: 800;
		line-height: 1;
	}

	/* Bar */
	.metric-bar-wrap { display: flex; flex-direction: column; gap: 0.25rem; }

	.metric-bar {
		height: 6px;
		background: rgba(0,0,0,0.08);
		border-radius: 4px;
		overflow: hidden;
	}

	.metric-bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.6s ease;
	}

	.bar-labels {
		display: flex;
		justify-content: space-between;
		font-size: 0.7rem;
		color: #aaa;
	}

	.metric-tag {
		align-self: flex-start;
		font-size: 0.78rem;
		font-weight: 700;
		padding: 0.25rem 0.65rem;
		border-radius: 20px;
	}

	.metric-note {
		margin: 0;
		font-size: 0.78rem;
		color: #888;
		line-height: 1.4;
	}

	/* ── RCI scale ── */
	.rci-scale { display: flex; flex-direction: column; gap: 0.25rem; }

	.rci-track {
		position: relative;
		height: 6px;
		background: rgba(0,0,0,0.08);
		border-radius: 4px;
	}

	.rci-center-line {
		position: absolute;
		left: 50%;
		top: -3px;
		width: 2px;
		height: 12px;
		background: rgba(0,0,0,0.2);
		border-radius: 2px;
		transform: translateX(-50%);
	}

	.rci-marker {
		position: absolute;
		top: 50%;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		transform: translate(-50%, -50%);
		transition: left 0.6s ease;
		box-shadow: 0 2px 4px rgba(0,0,0,0.2);
	}

	/* ── Trend row ── */
	.trend-row {
		display: flex;
		gap: 1.25rem;
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
	}

	.trend-card {
		flex: 1;
		min-width: 220px;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		display: flex;
		align-items: center;
		gap: 1.25rem;
		border: 1px solid rgba(0,0,0,0.06);
	}

	.trend-icon {
		font-size: 2.5rem;
		line-height: 1;
		font-weight: 900;
	}

	.trend-body { display: flex; flex-direction: column; gap: 0.25rem; }

	.trend-label {
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #777;
	}

	.trend-value {
		font-size: 1.1rem;
		font-weight: 800;
	}

	.trend-strength {
		font-size: 0.85rem;
		font-weight: 600;
		opacity: 0.75;
	}

	.trend-ewma {
		font-size: 0.78rem;
		color: #999;
	}

	/* ── Correlations ── */
	.correlations-section {
		border-top: 2px solid #f0f0f0;
		padding-top: 1.5rem;
		margin-bottom: 1.25rem;
	}

	.corr-title {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		color: #333;
	}

	.corr-subtitle {
		font-size: 0.8rem;
		color: #aaa;
		font-weight: 400;
	}

	.corr-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
		gap: 1rem;
	}

	.corr-card {
		background: #fafafa;
		border-radius: 14px;
		padding: 1rem 1.25rem;
		border: 1px solid #eee;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.corr-factor {
		font-size: 0.85rem;
		font-weight: 700;
		color: #444;
	}

	.corr-row {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.corr-dim {
		font-size: 0.72rem;
		color: #aaa;
		width: 72px;
		flex-shrink: 0;
	}

	.corr-bar-wrap {
		flex: 1;
		height: 6px;
		background: rgba(0,0,0,0.07);
		border-radius: 4px;
		overflow: hidden;
	}

	.corr-bar {
		height: 100%;
		border-radius: 4px;
		transition: width 0.6s ease;
	}

	.corr-r {
		font-size: 0.75rem;
		font-weight: 700;
		width: 54px;
		text-align: right;
	}

	.corr-interp {
		font-size: 0.72rem;
		color: #bbb;
	}

	/* ── Clinical legend ── */
	.clinical-legend {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
		padding-top: 1.25rem;
		border-top: 2px solid #f0f0f0;
		font-size: 0.75rem;
		color: #aaa;
	}

	.legend-item { display: flex; align-items: center; gap: 0.35rem; }

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.dot.green  { background: #4caf50; }
	.dot.amber  { background: #ff9800; }
	.dot.red    { background: #f44336; }

	.legend-sep { color: #ddd; }
	.legend-note { font-style: italic; }

	/* ── Responsive ── */
	@media (max-width: 640px) {
		.metrics-grid { grid-template-columns: 1fr; }
		.trend-row    { flex-direction: column; }
		.corr-grid    { grid-template-columns: 1fr; }
		.panel-header { flex-direction: column; }
	}
</style>
