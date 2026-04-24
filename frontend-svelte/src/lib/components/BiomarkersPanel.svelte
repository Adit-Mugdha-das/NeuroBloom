<script>
	import { locale, localeText, formatNumber, formatPercent } from '$lib/i18n';

	/** @type {any} */
	export let biomarkerData = null;
	export let doctorView = false;
	export let days = 30;

	const REQUIRED_SESSIONS = 3;
	const lt = (en, bn) => localeText({ en, bn }, $locale);

	function number(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function fixed(value, digits = 2) {
		if (value === null || value === undefined || !Number.isFinite(Number(value))) {
			return '—';
		}

		return number(Number(value), {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		});
	}

	function signedFixed(value, digits = 2) {
		if (value === null || value === undefined || !Number.isFinite(Number(value))) {
			return '—';
		}

		const sign = Number(value) > 0 ? '+' : '';
		return `${sign}${fixed(value, digits)}`;
	}

	function percent(value, digits = 0) {
		return formatPercent(value, $locale, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		});
	}

	function milliseconds(value, digits = 0) {
		if (value === null || value === undefined || !Number.isFinite(Number(value))) {
			return '—';
		}

		return `${number(value, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		})} ${lt('ms', 'মি.সে.')}`;
	}

	function getFatigueLevel(index) {
		if (index === null || index === undefined) return null;
		if (index > 0.5) {
			return {
				label: lt('High', 'বেশি'),
				color: '#f44336',
				bg: '#ffebee',
				pct: Math.min(100, index * 100)
			};
		}
		if (index > 0.3) {
			return {
				label: lt('Moderate', 'মাঝারি'),
				color: '#ff9800',
				bg: '#fff3e0',
				pct: Math.min(100, index * 100)
			};
		}
		return {
			label: lt('Low', 'কম'),
			color: '#4caf50',
			bg: '#e8f5e9',
			pct: Math.min(100, index * 100)
		};
	}

	function getCVLevel(cv) {
		if (cv === null || cv === undefined) return null;
		if (cv > 0.35) {
			return {
				label: lt('High variability', 'অনেক ওঠানামা'),
				color: '#f44336',
				bg: '#ffebee',
				pct: Math.min(100, cv * 200)
			};
		}
		if (cv > 0.25) {
			return {
				label: lt('Moderate variability', 'মাঝারি ওঠানামা'),
				color: '#ff9800',
				bg: '#fff3e0',
				pct: Math.min(100, cv * 200)
			};
		}
		return {
			label: lt('Normal consistency', 'স্বাভাবিক ধারাবাহিকতা'),
			color: '#4caf50',
			bg: '#e8f5e9',
			pct: Math.min(100, cv * 200)
		};
	}

	function getRCIInfo(rci) {
		if (rci === null || rci === undefined) return null;
		if (rci > 1.96) {
			return {
				label: lt('Significant improvement', 'উল্লেখযোগ্য উন্নতি'),
				icon: '+',
				color: '#4caf50',
				bg: '#e8f5e9'
			};
		}
		if (rci < -1.96) {
			return {
				label: lt('Significant decline', 'উল্লেখযোগ্য অবনতি'),
				icon: '-',
				color: '#f44336',
				bg: '#ffebee'
			};
		}
		return {
			label: lt('Stable, no significant change', 'স্থিতিশীল, বড় পরিবর্তন নেই'),
			icon: '=',
			color: '#667eea',
			bg: '#f0f2ff'
		};
	}

	function getTrendInfo(direction) {
		const key = String(direction || '').toLowerCase();
		if (key === 'improving') {
			return { icon: '↗', label: lt('Improving', 'উন্নতির দিকে'), color: '#4caf50', bg: '#e8f5e9' };
		}
		if (key === 'declining') {
			return { icon: '↘', label: lt('Declining', 'কমতির দিকে'), color: '#f44336', bg: '#ffebee' };
		}
		return { icon: '→', label: lt('Stable', 'স্থিতিশীল'), color: '#667eea', bg: '#f0f2ff' };
	}

	function trendStrength(strength) {
		const key = String(strength || '').toLowerCase();
		if (key === 'strong') return lt('strong', 'শক্তিশালী');
		if (key === 'moderate') return lt('moderate', 'মাঝারি');
		if (key === 'weak') return lt('weak', 'দুর্বল');
		return '';
	}

	function corrBar(r) {
		return Math.min(100, Math.abs(r || 0) * 100);
	}

	function corrColor(r) {
		const abs = Math.abs(r || 0);
		if (abs >= 0.6) return '#f44336';
		if (abs >= 0.3) return '#ff9800';
		return '#4caf50';
	}

	function corrLabel(r) {
		if (!r) return lt('Not enough data', 'যথেষ্ট ডেটা নেই');
		const abs = Math.abs(r);
		if (abs >= 0.6) {
			return r < 0
				? lt('Strong negative effect', 'শক্তিশালী নেতিবাচক প্রভাব')
				: lt('Strong positive effect', 'শক্তিশালী ইতিবাচক প্রভাব');
		}
		if (abs >= 0.3) {
			return r < 0
				? lt('Moderate negative effect', 'মাঝারি নেতিবাচক প্রভাব')
				: lt('Moderate positive effect', 'মাঝারি ইতিবাচক প্রভাব');
		}
		return lt('Weak relationship', 'দুর্বল সম্পর্ক');
	}

	function fatigueTitle() {
		return doctorView
			? lt('Fatigue Index', 'ক্লান্তি সূচক')
			: lt('Brain Fatigue Level', 'মস্তিষ্কের ক্লান্তির মাত্রা');
	}

	function cvTitle() {
		return doctorView
			? lt('Coefficient of Variation (CV)', 'ভ্যারিয়েশনের সহগ (CV)')
			: lt('Response Consistency', 'প্রতিক্রিয়ার ধারাবাহিকতা');
	}

	function rciTitle() {
		return doctorView
			? lt('Reliable Change Index (RCI)', 'নির্ভরযোগ্য পরিবর্তন সূচক (RCI)')
			: lt('Performance Change', 'পারফরম্যান্সের পরিবর্তন');
	}

	function trendTitle() {
		return doctorView
			? lt('EWMA Trend Analysis', 'EWMA ট্রেন্ড বিশ্লেষণ')
			: lt('Overall Trend', 'সামগ্রিক ধারা');
	}

	function patientRciNote() {
		if (rciVal > 1.96) {
			return lt(
				'Your recent scores are clearly above your starting point.',
				'আপনার সাম্প্রতিক স্কোর শুরুর অবস্থার তুলনায় স্পষ্টভাবে ভালো।'
			);
		}
		if (rciVal < -1.96) {
			return lt(
				'Your recent scores are lower than your starting point, so it may be worth discussing.',
				'আপনার সাম্প্রতিক স্কোর শুরুর অবস্থার তুলনায় কম; প্রয়োজনে চিকিৎসকের সঙ্গে আলোচনা করা ভালো।'
			);
		}
		return lt(
			'Comparing your current scores to your starting point.',
			'আপনার বর্তমান স্কোরকে শুরুর অবস্থার সঙ্গে তুলনা করা হচ্ছে।'
		);
	}

	function correlationSampleText(sampleSize) {
		return lt(`n=${number(sampleSize)}`, `n=${number(sampleSize)}`);
	}

	$: fatigue = biomarkerData?.fatigue_index?.mean ?? null;
	$: cv = biomarkerData?.rt_coefficient_of_variation?.mean ?? null;
	$: rciVal = biomarkerData?.reliable_change_index?.value ?? null;
	$: trend = biomarkerData?.performance_trend ?? null;
	$: rtTrend = biomarkerData?.rt_trend ?? null;
	$: fatCorr = biomarkerData?.fatigue_correlation ?? null;
	$: sleepCorr = biomarkerData?.sleep_correlation ?? null;
	$: medCorr = biomarkerData?.medication_timing_correlation ?? null;
	$: totalSessions = biomarkerData?.total_sessions ?? 0;

	$: fatigueInfo = getFatigueLevel(fatigue);
	$: cvInfo = getCVLevel(cv);
	$: rciInfo = getRCIInfo(rciVal);
	$: trendInfo = trend ? getTrendInfo(trend.direction) : null;
	$: rtTrendInfo = rtTrend ? getTrendInfo(rtTrend.direction) : null;
	$: remainingSessions = Math.max(REQUIRED_SESSIONS - totalSessions, 0);
	$: hasData = biomarkerData && totalSessions >= REQUIRED_SESSIONS;
</script>

<div class="biomarkers-panel">
	<div class="panel-header">
		<div class="header-left">
			<h3>{doctorView ? lt('MS Digital Biomarkers', 'MS ডিজিটাল বায়োমার্কার') : lt('Brain Health Indicators', 'মস্তিষ্কের স্বাস্থ্যসূচক')}</h3>
			<p class="subtitle">
				{doctorView
					? lt(
						`Clinical metrics extracted from ${number(totalSessions)} sessions · Last ${number(days)} days`,
						`${number(totalSessions)} সেশন থেকে নেওয়া ক্লিনিক্যাল মেট্রিক · শেষ ${number(days)} দিন`
					)
					: lt(
						`Based on your last ${number(days)} days of training · ${number(totalSessions)} sessions`,
						`শেষ ${number(days)} দিনের ট্রেনিং ও ${number(totalSessions)} সেশনের ভিত্তিতে`
					)}
			</p>
		</div>
		{#if doctorView}
			<div class="research-badge">{lt('Research Grade', 'গবেষণামানের')}</div>
		{/if}
	</div>

	{#if !hasData}
		<div class="no-data-state">
			<div class="no-data-icon">...</div>
			<p class="no-data-title">
				{remainingSessions > 0
					? lt(
						`${number(remainingSessions)} more session${remainingSessions === 1 ? '' : 's'} needed`,
						`আর ${number(remainingSessions)}টি সেশন দরকার`
					)
					: lt('No data available yet', 'এখনও পর্যাপ্ত ডেটা নেই')}
			</p>
			<p class="no-data-sub">
				{doctorView
					? lt(
						'Complete at least 3 training sessions to generate MS biomarkers.',
						'MS বায়োমার্কার তৈরি করতে অন্তত ৩টি ট্রেনিং সেশন সম্পন্ন করতে হবে।'
					)
					: lt(
						'Keep training. Brain health indicators unlock after 3 sessions.',
						'ট্রেনিং চালিয়ে যান। ৩টি সেশন শেষ হলে স্বাস্থ্যসূচক দেখা যাবে।'
					)}
			</p>
		</div>
	{:else}
		<div class="metrics-grid">
			<div class="metric-card" style="--card-bg: {fatigueInfo?.bg ?? '#f5f5f5'}">
				<div class="metric-header">
					<span class="metric-icon">FI</span>
					<span class="metric-title">{fatigueTitle()}</span>
				</div>
				<div class="metric-value" style="color: {fatigueInfo?.color ?? '#666'}">{fixed(fatigue, 2)}</div>
				<div class="metric-bar-wrap">
					<div class="metric-bar">
						<div
							class="metric-bar-fill"
							style="width: {fatigueInfo?.pct ?? 0}%; background: {fatigueInfo?.color ?? '#ccc'}"
						></div>
					</div>
					<span class="bar-labels"><span>{lt('None', 'নেই')}</span><span>{lt('Severe', 'তীব্র')}</span></span>
				</div>
				<div class="metric-tag" style="color: {fatigueInfo?.color}; background: {fatigueInfo?.bg}">
					{fatigueInfo?.label ?? '—'}
				</div>
				<p class="metric-note">
					{doctorView
						? lt(
							'>0.5 = severe fatigue · may indicate relapse or poor disease control',
							'>০.৫ = তীব্র ক্লান্তি · রিল্যাপস বা রোগনিয়ন্ত্রণ দুর্বল হওয়ার ইঙ্গিত হতে পারে'
						)
						: (fatigue ?? 0) > 0.4
							? lt(
								'You tend to tire during tasks. Rest before training can help.',
								'টাস্কের সময় আপনি দ্রুত ক্লান্ত হন। ট্রেনিংয়ের আগে বিশ্রাম নিলে সাহায্য হতে পারে।'
							)
							: lt(
								'Good energy levels maintained throughout tasks.',
								'টাস্কের পুরো সময় জুড়ে শক্তির মাত্রা ভালো ছিল।'
							)}
				</p>
			</div>

			<div class="metric-card" style="--card-bg: {cvInfo?.bg ?? '#f5f5f5'}">
				<div class="metric-header">
					<span class="metric-icon">CV</span>
					<span class="metric-title">{cvTitle()}</span>
				</div>
				<div class="metric-value" style="color: {cvInfo?.color ?? '#666'}">{fixed(cv, 3)}</div>
				<div class="metric-bar-wrap">
					<div class="metric-bar">
						<div
							class="metric-bar-fill"
							style="width: {cvInfo?.pct ?? 0}%; background: {cvInfo?.color ?? '#ccc'}"
						></div>
					</div>
					<span class="bar-labels"><span>{lt('Consistent', 'ধারাবাহিক')}</span><span>{lt('Erratic', 'অনিয়মিত')}</span></span>
				</div>
				<div class="metric-tag" style="color: {cvInfo?.color}; background: {cvInfo?.bg}">
					{cvInfo?.label ?? '—'}
				</div>
				<p class="metric-note">
					{doctorView
						? lt(
							'CV >0.35 = clinically significant RT variability · IIV MS biomarker',
							'CV >০.৩৫ = ক্লিনিক্যালি গুরুত্বপূর্ণ RT ভ্যারিয়েবিলিটি · IIV MS বায়োমার্কার'
						)
						: (cv ?? 0) > 0.3
							? lt(
								'Your response times vary quite a bit. This can happen in MS.',
								'আপনার প্রতিক্রিয়ার সময় কিছুটা ওঠানামা করছে। MS-এ এমন হতে পারে।'
							)
							: lt(
								'Your responses are fairly consistent. That is a good sign.',
								'আপনার প্রতিক্রিয়া বেশ ধারাবাহিক। এটি ভালো লক্ষণ।'
							)}
				</p>
			</div>

			<div class="metric-card" style="--card-bg: {rciInfo?.bg ?? '#f5f5f5'}">
				<div class="metric-header">
					<span class="metric-icon">{rciInfo?.icon ?? 'RCI'}</span>
					<span class="metric-title">{rciTitle()}</span>
				</div>
				<div class="metric-value" style="color: {rciInfo?.color ?? '#666'}">{signedFixed(rciVal, 2)}</div>
				<div class="rci-scale">
					<div class="rci-track">
						<div class="rci-center-line"></div>
						<div
							class="rci-marker"
							style="left: calc(50% + {Math.min(50, Math.max(-50, (rciVal ?? 0) * 12.75))}%); background: {rciInfo?.color}"
						></div>
					</div>
					<span class="bar-labels"><span>{lt('Declining', 'কমছে')}</span><span>{lt('Improving', 'উন্নতি')}</span></span>
				</div>
				<div class="metric-tag" style="color: {rciInfo?.color}; background: {rciInfo?.bg}">
					{rciInfo?.label ?? '—'}
				</div>
				<p class="metric-note">
					{doctorView
						? lt(
							'|RCI| >1.96 = statistically significant change',
							'|RCI| >১.৯৬ = পরিসংখ্যানগতভাবে উল্লেখযোগ্য পরিবর্তন'
						)
						: patientRciNote()}
				</p>
			</div>
		</div>

		<div class="trend-row">
			<div class="trend-card" style="background: {trendInfo?.bg ?? '#f0f2ff'}">
				<div class="trend-icon" style="color: {trendInfo?.color}">{trendInfo?.icon ?? '→'}</div>
				<div class="trend-body">
					<div class="trend-label">{trendTitle()}</div>
					<div class="trend-value" style="color: {trendInfo?.color}">
						{trendInfo?.label ?? lt('Stable', 'স্থিতিশীল')}
						{#if trendStrength(trend?.strength)}
							<span class="trend-strength">· {trendStrength(trend?.strength)}</span>
						{/if}
					</div>
					{#if trend?.current_ewma}
						<div class="trend-ewma">
							{lt('Current EWMA', 'বর্তমান EWMA')}: {fixed(trend.current_ewma, 1)}
						</div>
					{/if}
				</div>
			</div>

			{#if doctorView && rtTrendInfo}
				<div class="trend-card" style="background: {rtTrendInfo?.bg ?? '#f0f2ff'}">
					<div class="trend-icon" style="color: {rtTrendInfo?.color}">{rtTrendInfo?.icon ?? '→'}</div>
					<div class="trend-body">
						<div class="trend-label">{lt('Reaction Time Trend', 'প্রতিক্রিয়া সময়ের ধারা')}</div>
						<div class="trend-value" style="color: {rtTrendInfo?.color}">
							{rtTrendInfo?.label ?? lt('Stable', 'স্থিতিশীল')}
							{#if trendStrength(rtTrend?.strength)}
								<span class="trend-strength">· {trendStrength(rtTrend?.strength)}</span>
							{/if}
						</div>
						{#if rtTrend?.current_ewma}
							<div class="trend-ewma">
								{lt('Current EWMA', 'বর্তমান EWMA')}: {milliseconds(rtTrend.current_ewma, 0)}
							</div>
						{/if}
					</div>
				</div>
			{/if}
		</div>

		{#if doctorView && (fatCorr?.sample_size >= 3 || sleepCorr?.sample_size >= 3 || medCorr?.sample_size >= 3)}
			<div class="correlations-section">
				<h4 class="corr-title">
					{lt('Contextual Correlations', 'প্রাসঙ্গিক সম্পর্ক')}
					<span class="corr-subtitle">
						{lt('(Pearson r, how each factor affects performance)', '(Pearson r, কোন বিষয় পারফরম্যান্সে কতটা প্রভাব ফেলে)')}
					</span>
				</h4>
				<div class="corr-grid">
					{#if fatCorr?.sample_size >= 3}
						<div class="corr-card">
							<div class="corr-factor">{lt('Fatigue Level', 'ক্লান্তির মাত্রা')}</div>
							<div class="corr-row">
								<span class="corr-dim">{lt('Score impact', 'স্কোরে প্রভাব')}</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(fatCorr.correlation_with_score)}%; background: {corrColor(fatCorr.correlation_with_score)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(fatCorr.correlation_with_score)}">{lt('r =', 'r =')} {fixed(fatCorr.correlation_with_score ?? 0, 2)}</span>
							</div>
							<div class="corr-row">
								<span class="corr-dim">{lt('RT impact', 'RT প্রভাব')}</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(fatCorr.correlation_with_rt)}%; background: {corrColor(fatCorr.correlation_with_rt)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(fatCorr.correlation_with_rt)}">{lt('r =', 'r =')} {fixed(fatCorr.correlation_with_rt ?? 0, 2)}</span>
							</div>
							<div class="corr-interp">{corrLabel(fatCorr.correlation_with_score)} · {correlationSampleText(fatCorr.sample_size)}</div>
						</div>
					{/if}

					{#if sleepCorr?.sample_size >= 3}
						<div class="corr-card">
							<div class="corr-factor">{lt('Sleep Quality', 'ঘুমের মান')}</div>
							<div class="corr-row">
								<span class="corr-dim">{lt('Score impact', 'স্কোরে প্রভাব')}</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(sleepCorr.correlation_with_score)}%; background: {corrColor(sleepCorr.correlation_with_score)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(sleepCorr.correlation_with_score)}">{lt('r =', 'r =')} {fixed(sleepCorr.correlation_with_score ?? 0, 2)}</span>
							</div>
							<div class="corr-row">
								<span class="corr-dim">{lt('RT impact', 'RT প্রভাব')}</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(sleepCorr.correlation_with_rt)}%; background: {corrColor(sleepCorr.correlation_with_rt)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(sleepCorr.correlation_with_rt)}">{lt('r =', 'r =')} {fixed(sleepCorr.correlation_with_rt ?? 0, 2)}</span>
							</div>
							<div class="corr-interp">{corrLabel(sleepCorr.correlation_with_score)} · {correlationSampleText(sleepCorr.sample_size)}</div>
						</div>
					{/if}

					{#if medCorr?.sample_size >= 3}
						<div class="corr-card">
							<div class="corr-factor">{lt('Medication Timing', 'ওষুধ নেওয়ার সময়')}</div>
							<div class="corr-row">
								<span class="corr-dim">{lt('Score impact', 'স্কোরে প্রভাব')}</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(medCorr.correlation_with_score)}%; background: {corrColor(medCorr.correlation_with_score)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(medCorr.correlation_with_score)}">{lt('r =', 'r =')} {fixed(medCorr.correlation_with_score ?? 0, 2)}</span>
							</div>
							<div class="corr-row">
								<span class="corr-dim">{lt('RT impact', 'RT প্রভাব')}</span>
								<div class="corr-bar-wrap">
									<div class="corr-bar" style="width: {corrBar(medCorr.correlation_with_rt)}%; background: {corrColor(medCorr.correlation_with_rt)}"></div>
								</div>
								<span class="corr-r" style="color: {corrColor(medCorr.correlation_with_rt)}">{lt('r =', 'r =')} {fixed(medCorr.correlation_with_rt ?? 0, 2)}</span>
							</div>
							<div class="corr-interp">{corrLabel(medCorr.correlation_with_score)} · {correlationSampleText(medCorr.sample_size)}</div>
						</div>
					{/if}
				</div>
			</div>
		{/if}

		{#if doctorView}
			<div class="clinical-legend">
				<span class="legend-item"><span class="dot green"></span> {lt('Normal / Improving', 'স্বাভাবিক / উন্নতির দিকে')}</span>
				<span class="legend-item"><span class="dot amber"></span> {lt('Moderate / Watch', 'মাঝারি / নজরে রাখুন')}</span>
				<span class="legend-item"><span class="dot red"></span> {lt('High / Declining', 'বেশি / কমতির দিকে')}</span>
				<span class="legend-sep">|</span>
				<span class="legend-note">{lt('Based on BICAMS standards · RCI threshold ±1.96', 'BICAMS মানদণ্ডভিত্তিক · RCI সীমা ±১.৯৬')}</span>
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
		line-height: 1.5;
	}

	.research-badge {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		font-size: 0.75rem;
		font-weight: 700;
		padding: 0.35rem 0.85rem;
		border-radius: 20px;
		white-space: nowrap;
	}

	.no-data-state {
		text-align: center;
		padding: 3rem 2rem;
		color: #888;
	}

	.no-data-icon {
		font-size: 2rem;
		margin-bottom: 1rem;
		letter-spacing: 0.2em;
	}

	.no-data-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #666;
		margin: 0 0 0.5rem 0;
	}

	.no-data-sub {
		font-size: 0.9rem;
		color: #777;
		margin: 0;
	}

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
		border: 1px solid rgba(0, 0, 0, 0.06);
	}

	.metric-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		font-weight: 700;
		color: #555;
	}

	.metric-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 2rem;
		min-height: 2rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.72);
		font-size: 0.72rem;
		font-weight: 800;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 800;
		line-height: 1;
	}

	.metric-bar-wrap,
	.rci-scale {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.metric-bar,
	.rci-track {
		height: 6px;
		background: rgba(0, 0, 0, 0.08);
		border-radius: 4px;
		position: relative;
	}

	.metric-bar {
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
		color: #777;
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
		color: #666;
		line-height: 1.45;
	}

	.rci-center-line {
		position: absolute;
		left: 50%;
		top: -3px;
		width: 2px;
		height: 12px;
		background: rgba(0, 0, 0, 0.2);
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
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

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
		border: 1px solid rgba(0, 0, 0, 0.06);
	}

	.trend-icon {
		font-size: 2.25rem;
		line-height: 1;
		font-weight: 900;
	}

	.trend-body {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.trend-label {
		font-size: 0.75rem;
		font-weight: 700;
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
		color: #777;
	}

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
		color: #777;
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
		color: #777;
		width: 72px;
		flex-shrink: 0;
	}

	.corr-bar-wrap {
		flex: 1;
		height: 6px;
		background: rgba(0, 0, 0, 0.07);
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
		color: #777;
	}

	.clinical-legend {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
		padding-top: 1.25rem;
		border-top: 2px solid #f0f0f0;
		font-size: 0.75rem;
		color: #777;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.dot.green {
		background: #4caf50;
	}

	.dot.amber {
		background: #ff9800;
	}

	.dot.red {
		background: #f44336;
	}

	.legend-sep {
		color: #ddd;
	}

	.legend-note {
		font-style: italic;
	}

	@media (max-width: 640px) {
		.biomarkers-panel {
			padding: 1.25rem;
		}

		.metrics-grid,
		.corr-grid {
			grid-template-columns: 1fr;
		}

		.trend-row,
		.panel-header {
			flex-direction: column;
		}
	}
</style>
