<script>
	import { goto } from '$app/navigation';
	import { baseline, patientJourney } from '$lib/api';
	import { BASELINE_MODULES, getNextBaselineModule } from '$lib/baseline-flow';
	import { locale, localeText, locale as activeLocale, uiText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let journey = null;
	let baselineData = null;
	let calculating = false;
	let error = null;

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	user.subscribe((value) => {
		currentUser = value;
	});

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadBaselineWorkspace();
	});

	async function loadBaselineWorkspace() {
		loading = true;
		error = null;

		try {
			journey = await patientJourney.get(currentUser.id);
			const baselineResponse = await baseline.get(currentUser.id);
			baselineData = baselineResponse?.assessment || null;

			if (journey?.state === 'training_ready' || journey?.state === 'training_in_session' || journey?.state === 'progress_available') {
				goto('/training');
				return;
			}
		} catch (loadError) {
			console.error('Error loading baseline workspace:', loadError);
			error = lt(
				'We could not load your baseline workspace right now.',
				'এই মুহূর্তে আপনার বেসলাইন ওয়ার্কস্পেস লোড করা যাচ্ছে না।'
			);
		} finally {
			loading = false;
		}
	}

	async function calculateBaseline() {
		calculating = true;
		error = null;

		try {
			await baseline.calculate(currentUser.id);
			await loadBaselineWorkspace();
			goto('/baseline/results');
		} catch (loadError) {
			error =
				loadError?.response?.data?.detail ||
				lt(
					'Complete all baseline modules before calculating your baseline.',
					'বেসলাইন ক্যালকুলেট করার আগে সব বেসলাইন মডিউল সম্পন্ন করুন।'
				);
		} finally {
			calculating = false;
		}
	}

	const getStatusLabel = (completed) =>
		completed ? lt('Completed', 'সম্পন্ন') : lt('Not started', 'শুরু হয়নি');

	$: taskStatus = journey?.baseline?.tasks || {};
	$: nextModule = getNextBaselineModule(taskStatus);
	$: allCompleted = !!journey?.baseline?.all_completed;
</script>

<div class="baseline-shell">
	{#if loading}
		<section class="state-card">
			<p>{lt('Loading your baseline workspace...', 'আপনার বেসলাইন ওয়ার্কস্পেস লোড হচ্ছে...')}</p>
		</section>
	{:else if error}
		<section class="state-card error-card">
			<h2>{lt('Baseline workspace unavailable', 'বেসলাইন ওয়ার্কস্পেস পাওয়া যাচ্ছে না')}</h2>
			<p>{error}</p>
			<button class="primary-btn" on:click={loadBaselineWorkspace}>{lt('Retry', 'পুনরায় চেষ্টা করুন')}</button>
		</section>
	{:else}
		<header class="hero-card">
			<div>
				<p class="eyebrow">{uiText("NeuroBloom Baseline", $activeLocale)}</p>
				<h1>{lt('Your six-step baseline assessment', 'আপনার ছয়-ধাপের বেসলাইন মূল্যায়ন')}</h1>
				<p class="hero-copy">
					{lt(
						'Complete each domain once so the app can calculate your baseline and generate a real training plan.',
						'প্রতিটি ডোমেইন একবার সম্পন্ন করুন, যাতে অ্যাপ আপনার বেসলাইন ক্যালকুলেট করে একটি বাস্তব ট্রেনিং প্ল্যান তৈরি করতে পারে।'
					)}
				</p>
			</div>
			<div class="hero-actions">
				<button class="ghost-btn" on:click={() => goto('/dashboard')}>{lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}</button>
				{#if nextModule}
					<a class="primary-link" href={nextModule.route}>{lt('Start Next Task', 'পরের টাস্ক শুরু করুন')}</a>
				{:else if allCompleted && !baselineData}
					<button class="primary-btn" on:click={calculateBaseline} disabled={calculating}>
						{calculating ? lt('Calculating...', 'ক্যালকুলেট হচ্ছে...') : lt('Calculate Baseline', 'বেসলাইন ক্যালকুলেট করুন')}
					</button>
				{:else if baselineData}
					<a class="primary-link" href="/baseline/results">{lt('View Baseline Results', 'বেসলাইন রেজাল্ট দেখুন')}</a>
				{/if}
			</div>
		</header>

		<section class="summary-grid">
			<article class="summary-card">
				<p class="summary-label">{lt('Progress', 'অগ্রগতি')}</p>
				<strong>{journey?.baseline?.completed_count || 0} / {journey?.baseline?.total_tasks || 6}</strong>
				<p>{lt('Completed baseline modules', 'সম্পন্ন বেসলাইন মডিউল')}</p>
			</article>
			<article class="summary-card">
				<p class="summary-label">{lt('Next Step', 'পরের ধাপ')}</p>
				<strong>
					{nextModule
						? localeText(nextModule.title, $locale)
						: baselineData
							? lt('Training Plan', 'ট্রেনিং প্ল্যান')
							: lt('Calculate Baseline', 'বেসলাইন ক্যালকুলেট করুন')}
				</strong>
				<p>
					{nextModule
						? lt('Complete the next incomplete domain.', 'পরের অসম্পূর্ণ ডোমেইনটি সম্পন্ন করুন।')
						: baselineData
							? lt('You can continue into training.', 'এখন আপনি ট্রেনিংয়ে এগোতে পারবেন।')
							: lt('Your six modules are done.', 'আপনার ছয়টি মডিউল সম্পন্ন হয়েছে।')}
				</p>
			</article>
		</section>

		<section class="modules-grid">
			{#each BASELINE_MODULES as module}
				<article class:completed={taskStatus[module.key]} class="module-card">
					<div class="module-head">
						<div>
							<p class="module-label">{localeText(module.title, $locale)}</p>
							<h2>{getStatusLabel(taskStatus[module.key])}</h2>
						</div>
						<span class="status-pill">{taskStatus[module.key] ? lt('Done', 'সম্পন্ন') : lt('Pending', 'বাকি')}</span>
					</div>
					<p class="module-copy">{localeText(module.description, $locale)}</p>
					<a class="module-link" href={module.route}>
						{taskStatus[module.key] ? lt('Replay Module', 'আবার মডিউল চালু করুন') : lt('Open Module', 'মডিউল খুলুন')}
					</a>
				</article>
			{/each}
		</section>
	{/if}
</div>

<style>
	.baseline-shell {
		min-height: 100vh;
		padding: 1.5rem;
		background:
			radial-gradient(circle at top left, rgba(14, 165, 233, 0.12), transparent 26%),
			radial-gradient(circle at right top, rgba(34, 197, 94, 0.12), transparent 24%),
			linear-gradient(135deg, #eff6ff, #f8fafc);
		display: grid;
		gap: 1rem;
	}

	.hero-card,
	.summary-card,
	.module-card,
	.state-card {
		max-width: 1180px;
		margin: 0 auto;
		width: 100%;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(226, 232, 240, 0.8);
		border-radius: 24px;
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
	}

	.hero-card {
		padding: 1.5rem;
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.eyebrow,
	.summary-label,
	.module-label {
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 0.78rem;
		font-weight: 800;
		color: #2563eb;
	}

	.hero-card h1,
	.module-card h2,
	.state-card h2 {
		margin: 0.25rem 0 0;
		color: #0f172a;
	}

	.hero-copy,
	.summary-card p,
	.module-copy,
	.state-card p {
		color: #475569;
		line-height: 1.55;
	}

	.hero-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.primary-link,
	.primary-btn,
	.ghost-btn,
	.module-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 999px;
		padding: 0.8rem 1.15rem;
		font-weight: 700;
		text-decoration: none;
		cursor: pointer;
	}

	.primary-link,
	.primary-btn,
	.module-link {
		background: linear-gradient(135deg, #2563eb, #1d4ed8);
		color: #fff;
		border: none;
	}

	.ghost-btn {
		background: rgba(255, 255, 255, 0.92);
		border: 1px solid rgba(148, 163, 184, 0.5);
		color: #0f172a;
	}

	.summary-grid,
	.modules-grid {
		max-width: 1180px;
		margin: 0 auto;
		width: 100%;
		display: grid;
		gap: 1rem;
	}

	.summary-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.modules-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.summary-card,
	.module-card,
	.state-card {
		padding: 1.25rem;
	}

	.module-card.completed {
		border-color: rgba(34, 197, 94, 0.35);
	}

	.module-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.status-pill {
		padding: 0.4rem 0.7rem;
		border-radius: 999px;
		background: rgba(37, 99, 235, 0.12);
		color: #1d4ed8;
		font-size: 0.78rem;
		font-weight: 700;
	}

	.error-card {
		text-align: center;
	}

	@media (max-width: 860px) {
		.baseline-shell {
			padding: 1rem;
		}

		.hero-card,
		.summary-grid,
		.modules-grid {
			grid-template-columns: 1fr;
		}

		.hero-card {
			flex-direction: column;
		}
	}
</style>
