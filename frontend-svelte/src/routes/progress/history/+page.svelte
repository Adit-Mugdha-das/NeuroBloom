<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { formatDateTime, formatNumber, formatPercent, locale, localeText } from '$lib/i18n';
	import { formatDuration, formatShortDate, getDomainName, getScoreColor } from '$lib/progress';
	import { user } from '$lib/stores';
	import { downloadCSV } from '$lib/utils/chartDownload';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let history = [];

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);
	const oneDecimal = (value) =>
		formatNumber(value, $locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	const pct = (value) => formatPercent(value, $locale, { maximumFractionDigits: 1 });

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadHistory();
	});

	async function loadHistory() {
		loading = true;
		error = null;

		try {
			history = await training.getHistory(currentUser.id, 30);
		} catch (loadError) {
			console.error('Error loading training history:', loadError);
			error = lt('Complete more training sessions to review history.', 'হিস্ট্রি দেখতে আরও কিছু ট্রেনিং সেশন সম্পন্ন করুন।');
		} finally {
			loading = false;
		}
	}

	function handleDownloadCsv() {
		if (!history.length) return;

		const exportRows = history.map((session) => ({
			date: formatShortDate(session.created_at, $locale),
			domain: getDomainName(session.domain, $locale),
			score: oneDecimal(session.score),
			accuracy: oneDecimal(session.accuracy),
			duration: formatDuration(session.duration, $locale)
		}));

		downloadCSV(exportRows, `training-history-${new Date().toISOString().split('T')[0]}`);
	}

	function handleDownloadPdf() {
		if (!history.length || typeof window === 'undefined') return;

		const reportRows = history
			.map(
				(session) => `
					<tr>
						<td>${formatShortDate(session.created_at, $locale)}</td>
						<td>${getDomainName(session.domain, $locale)}</td>
						<td>${oneDecimal(session.score)}</td>
						<td>${pct(session.accuracy)}</td>
						<td>${formatDuration(session.duration, $locale)}</td>
					</tr>`
			)
			.join('');

		const reportWindow = window.open('', '_blank', 'width=900,height=700');
		if (!reportWindow) return;

		reportWindow.document.write(`
			<html>
				<head>
					<title>${lt('NeuroBloom Training History Report', 'NeuroBloom ট্রেনিং হিস্ট্রি রিপোর্ট')}</title>
					<style>
						body { font-family: Arial, sans-serif; padding: 24px; color: #1f2937; }
						h1 { margin-bottom: 8px; }
						p { color: #475569; }
						table { width: 100%; border-collapse: collapse; margin-top: 20px; }
						th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; }
						th { background: #eef2ff; }
					</style>
				</head>
				<body>
					<h1>${lt('NeuroBloom Training History', 'NeuroBloom ট্রেনিং হিস্ট্রি')}</h1>
					<p>${lt('Generated on', 'তৈরি হয়েছে')} ${formatDateTime(new Date(), $locale)}</p>
					<table>
						<thead>
							<tr>
								<th>${lt('Date', 'তারিখ')}</th>
								<th>${lt('Domain', 'ডোমেইন')}</th>
								<th>${lt('Score', 'স্কোর')}</th>
								<th>${lt('Accuracy', 'নির্ভুলতা')}</th>
								<th>${lt('Duration', 'সময়')}</th>
							</tr>
						</thead>
						<tbody>${reportRows}</tbody>
					</table>
				</body>
			</html>
		`);
		reportWindow.document.close();
		reportWindow.focus();
		reportWindow.print();
	}
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
<<<<<<< HEAD
			<p>{lt('Loading training history...', 'ট্রেনিং হিস্ট্রি লোড হচ্ছে...')}</p>
=======
				<p>{lt('Loading training history...', 'ট্রেনিং হিস্ট্রি লোড হচ্ছে...')}</p>
			</section>
		{:else if error}
			<section class="state-panel glass-card">
				<h2>{lt('Training history unavailable', 'ট্রেনিং হিস্ট্রি পাওয়া যাচ্ছে না')}</h2>
				<p>{error}</p>
			</section>
		{:else if history.length === 0}
			<section class="state-panel glass-card">
				<h2>{lt('No sessions yet', 'এখনো কোনো সেশন নেই')}</h2>
				<p>{lt('Once you complete training sessions, they will appear here in a compact timeline.', 'ট্রেনিং সেশন সম্পন্ন করলে সেগুলো এখানে একটি সংক্ষিপ্ত টাইমলাইনে দেখা যাবে।')}</p>
			</section>
		{:else}
			<section class="glass-card list-shell">
				<div class="list-head">
					<div>
						<p class="card-label">{lt('Training history', 'ট্রেনিং হিস্ট্রি')}</p>
						<h2>{lt('Recent sessions', 'সাম্প্রতিক সেশন')}</h2>
					</div>
					<div class="list-actions">
						<p class="list-note">{lt('A compact record of your recent training sessions.', 'আপনার সাম্প্রতিক ট্রেনিং সেশনগুলোর একটি সংক্ষিপ্ত রেকর্ড।')}</p>
						<div class="action-row">
							<button class="action-btn" on:click={handleDownloadPdf}>{lt('PDF report', 'PDF রিপোর্ট')}</button>
							<button class="action-btn" on:click={handleDownloadCsv}>{lt('CSV export', 'CSV এক্সপোর্ট')}</button>
						</div>
					</div>
				</div>

			<div class="history-list">
				{#each history as session}
					<article class="history-row">
						<div class="history-main">
							<p class="row-domain">{getDomainName(session.domain, $locale)}</p>
							<p class="row-date">{formatShortDate(session.created_at, $locale)}</p>
						</div>
						<div class="history-metrics">
							<div>
								<p class="metric-label">{lt('Score', 'স্কোর')}</p>
								<p class="metric-value" style="color: {getScoreColor(session.score)}">{oneDecimal(session.score)}</p>
							</div>
							<div>
								<p class="metric-label">{lt('Accuracy', 'নির্ভুলতা')}</p>
								<p class="metric-value">{pct(session.accuracy)}</p>
							</div>
							<div>
								<p class="metric-label">{lt('Duration', 'সময়')}</p>
								<p class="metric-value">{formatDuration(session.duration, $locale)}</p>
							</div>
						</div>
					</article>
				{/each}
			</div>
>>>>>>> 3bf3510 (bangla interface refactoring)
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>{lt('Training history unavailable', 'ট্রেনিং হিস্ট্রি পাওয়া যাচ্ছে না')}</h2>
			<p>{error}</p>
		</section>
	{:else if history.length === 0}
		<section class="state-panel glass-card">
			<h2>{lt('No sessions yet', 'এখনো কোনো সেশন নেই')}</h2>
			<p>{lt('Once you complete training sessions, they will appear here in a compact timeline.', 'ট্রেনিং সেশন সম্পন্ন করলে সেগুলো এখানে একটি সংক্ষিপ্ত টাইমলাইনে দেখা যাবে।')}</p>
		</section>
	{:else}
		<div class="history-panel">
			<div class="glass-card history-header">
				<div class="header-copy">
					<p class="card-label">{lt('Training history', 'ট্রেনিং হিস্ট্রি')}</p>
					<h2>{lt('Recent sessions', 'সাম্প্রতিক সেশন')}</h2>
					<p class="header-note">{lt('A compact record of your recent training sessions.', 'আপনার সাম্প্রতিক ট্রেনিং সেশনগুলোর একটি সংক্ষিপ্ত রেকর্ড।')}</p>
				</div>
				<div class="action-row">
					<button class="action-btn" on:click={handleDownloadPdf}>{lt('PDF report', 'PDF রিপোর্ট')}</button>
					<button class="action-btn" on:click={handleDownloadCsv}>{lt('CSV export', 'CSV এক্সপোর্ট')}</button>
				</div>
			</div>

			{#each history as session}
				<article class="glass-card history-row">
					<div class="history-main">
						<p class="row-domain">{getDomainName(session.domain, $locale)}</p>
						<p class="row-date">{formatShortDate(session.created_at, $locale)}</p>
					</div>
					<div class="history-metrics">
						<div>
							<p class="metric-label">{lt('Score', 'স্কোর')}</p>
							<p class="metric-value" style="color: {getScoreColor(session.score)}">{session.score.toFixed(1)}</p>
						</div>
						<div>
							<p class="metric-label">{lt('Accuracy', 'নির্ভুলতা')}</p>
							<p class="metric-value">{session.accuracy.toFixed(1)}%</p>
						</div>
						<div>
							<p class="metric-label">{lt('Duration', 'সময়')}</p>
							<p class="metric-value">{formatDuration(session.duration, $locale)}</p>
						</div>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</div>

<style>
	.progress-panel {
		width: 100%;
	}

	.glass-card,
	.state-panel {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
		box-sizing: border-box;
	}

	.history-panel {
	width: 100%;
	margin: 0;
	display: grid;
	grid-template-columns: minmax(0, 1fr);
	gap: 0.75rem;
}

	.history-header,
	.history-row,
	.state-panel {
		width: 100%;
		box-sizing: border-box;
	}

	.card-label,
	.metric-label {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #64748b;
	}

	.history-header h2,
	.state-panel h2 {
		margin: 0.25rem 0 0;
		font-size: 1.7rem;
		color: #111827;
	}

	.history-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(79, 70, 229, 0.04) 100%);
		border-color: rgba(99, 102, 241, 0.22);
	}

	.header-copy {
		min-width: 0;
	}

	.header-note,
	.state-panel p {
		margin: 0.4rem 0 0;
		line-height: 1.55;
		color: #64748b;
		font-size: 0.9rem;
	}

	.action-row {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
		flex-shrink: 0;
	}

	.action-btn {
		border: none;
		border-radius: 999px;
		padding: 0.75rem 1rem;
		font-weight: 700;
		cursor: pointer;
		background: rgba(79, 70, 229, 0.12);
		color: #4338ca;
	}

	.history-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
		min-height: 78px;
	}

	.history-main {
		min-width: 0;
		flex: 1;
	}

	.row-domain {
		margin: 0;
		font-weight: 700;
		color: #111827;
		text-transform: capitalize;
	}

	.row-date {
		margin: 0.25rem 0 0;
		color: #64748b;
		font-size: 0.9rem;
	}

	.history-metrics {
		display: grid;
		grid-template-columns: repeat(3, minmax(90px, 1fr));
		gap: 1rem;
		flex: 0 0 55%;
	}

	.metric-value {
		margin: 0.25rem 0 0;
		font-weight: 700;
		color: #111827;
	}

	@media (max-width: 860px) {
		.history-panel {
			width: 100%;
		}

		.history-header,
		.history-row {
			flex-direction: column;
			align-items: flex-start;
		}

		.history-metrics {
			grid-template-columns: 1fr;
			flex: none;
			width: 100%;
		}
	}
</style>