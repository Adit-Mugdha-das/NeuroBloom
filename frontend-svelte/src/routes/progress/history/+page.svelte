<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
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
			error = 'Complete more training sessions to review history.';
		} finally {
			loading = false;
		}
	}

	function handleDownloadCsv() {
		if (!history.length) return;

		const exportRows = history.map((session) => ({
			date: formatShortDate(session.created_at),
			domain: getDomainName(session.domain),
			score: session.score.toFixed(1),
			accuracy: session.accuracy.toFixed(1),
			duration: formatDuration(session.duration)
		}));

		downloadCSV(exportRows, `training-history-${new Date().toISOString().split('T')[0]}`);
	}

	function handleDownloadPdf() {
		if (!history.length || typeof window === 'undefined') return;

		const reportRows = history
			.map(
				(session) => `
					<tr>
						<td>${formatShortDate(session.created_at)}</td>
						<td>${getDomainName(session.domain)}</td>
						<td>${session.score.toFixed(1)}</td>
						<td>${session.accuracy.toFixed(1)}%</td>
						<td>${formatDuration(session.duration)}</td>
					</tr>`
			)
			.join('');

		const reportWindow = window.open('', '_blank', 'width=900,height=700');
		if (!reportWindow) return;

		reportWindow.document.write(`
			<html>
				<head>
					<title>NeuroBloom Training History Report</title>
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
					<h1>NeuroBloom Training History</h1>
					<p>Generated on ${new Date().toLocaleString()}</p>
					<table>
						<thead>
							<tr>
								<th>Date</th>
								<th>Domain</th>
								<th>Score</th>
								<th>Accuracy</th>
								<th>Duration</th>
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
			<p>Loading training history...</p>
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>Training history unavailable</h2>
			<p>{error}</p>
		</section>
	{:else if history.length === 0}
		<section class="state-panel glass-card">
			<h2>No sessions yet</h2>
			<p>Once you complete training sessions, they will appear here in a compact timeline.</p>
		</section>
	{:else}
		<section class="glass-card list-shell">
			<div class="list-head">
				<div>
					<p class="card-label">Training History</p>
					<h2>Recent sessions</h2>
				</div>
				<div class="list-actions">
					<p class="list-note">A compact record of your recent training sessions.</p>
					<div class="action-row">
						<button class="action-btn" on:click={handleDownloadPdf}>PDF Report</button>
						<button class="action-btn" on:click={handleDownloadCsv}>CSV Export</button>
					</div>
				</div>
			</div>

			<div class="history-list">
				{#each history as session}
					<article class="history-row">
						<div class="history-main">
							<p class="row-domain">{getDomainName(session.domain)}</p>
							<p class="row-date">{formatShortDate(session.created_at)}</p>
						</div>
						<div class="history-metrics">
							<div>
								<p class="metric-label">Score</p>
								<p class="metric-value" style="color: {getScoreColor(session.score)}">{session.score.toFixed(1)}</p>
							</div>
							<div>
								<p class="metric-label">Accuracy</p>
								<p class="metric-value">{session.accuracy.toFixed(1)}%</p>
							</div>
							<div>
								<p class="metric-label">Duration</p>
								<p class="metric-value">{formatDuration(session.duration)}</p>
							</div>
						</div>
					</article>
				{/each}
			</div>
		</section>
	{/if}
</div>

<style>
	.glass-card,
	.state-panel {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	}

	.list-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 1rem;
		margin-bottom: 1rem;
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

	.list-head h2,
	.state-panel h2 {
		margin: 0.25rem 0 0;
		font-size: 1.7rem;
		color: #111827;
	}

	.list-note,
	.state-panel p {
		margin: 0;
		line-height: 1.55;
		color: #64748b;
	}

	.list-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.action-row {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
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

	.history-list {
		display: grid;
		gap: 0.75rem;
	}

	.history-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
		padding: 1rem;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.72);
		border: 1px solid rgba(255, 255, 255, 0.8);
	}

	.row-domain {
		margin: 0;
		font-weight: 700;
		color: #111827;
	}

	.row-date {
		margin: 0.25rem 0 0;
		color: #64748b;
		font-size: 0.9rem;
	}

	.history-metrics {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1rem;
		min-width: 420px;
	}

	.metric-value {
		margin: 0.25rem 0 0;
		font-weight: 700;
		color: #111827;
	}

	@media (max-width: 860px) {
		.list-head,
		.history-row {
			flex-direction: column;
			align-items: flex-start;
		}

		.list-actions {
			justify-content: flex-start;
		}

		.history-metrics {
			grid-template-columns: 1fr;
			min-width: 0;
			width: 100%;
		}
	}
</style>