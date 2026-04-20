<script>
	import { training } from '$lib/api.js';
	import { locale, localeText } from '$lib/i18n';
	import { user } from '$lib/stores.js';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let showQuestionnaire = true;

	let fatigueLevel = 5;
	let sleepQuality = 5;
	let medicationTaken = null;
	let hoursSinceMedication = null;
	let readinessLevel = 7;

	let submitting = false;
	let error = '';
	let currentUser;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	async function submitQuestionnaire() {
		submitting = true;
		error = '';

		try {
			const response = await training.createSessionContext({
				user_id: currentUser.id,
				fatigue_level: fatigueLevel,
				sleep_quality: sleepQuality,
				sleep_hours: null,
				medication_taken_today: medicationTaken,
				hours_since_medication: hoursSinceMedication,
				pain_level: null,
				stress_level: null,
				readiness_level: readinessLevel,
				notes: null,
				location: null
			});

			dispatch('complete', {
				contextId: response.context_id,
				timeOfDay: response.time_of_day
			});

			showQuestionnaire = false;
		} catch (requestError) {
			error = lt(
				'Failed to save your answers. Please try again.',
				'আপনার উত্তর সংরক্ষণ করা যায়নি। আবার চেষ্টা করুন।'
			);
			console.error(requestError);
		} finally {
			submitting = false;
		}
	}

	function skip() {
		dispatch('skip');
		showQuestionnaire = false;
	}
</script>

{#if showQuestionnaire}
	<div class="questionnaire-overlay">
		<div class="questionnaire-modal">
			<div class="modal-header">
				<h2>{lt('Quick Check-In', 'দ্রুত চেক-ইন')}</h2>
				<p class="subtitle">{lt('A few short answers before this training session', 'এই ট্রেনিং সেশনের আগে কয়েকটি ছোট উত্তর দিন')}</p>
			</div>

			<div class="modal-body">
				{#if error}
					<div class="error-message">{error}</div>
				{/if}

				<div class="question-section">
					<h3>{lt('Session readiness', 'সেশন প্রস্তুতি')}</h3>

					<div class="question-group">
						<label for="fatigue-level">
							<span class="label-text">{lt('Energy level', 'শক্তির মাত্রা')}</span>
							<span class="label-value">{fatigueLevel}/10</span>
						</label>
						<div class="scale-labels">
							<span>{lt('Exhausted', 'ক্লান্ত')}</span>
							<span>{lt('Energized', 'শক্তিশালী')}</span>
						</div>
						<input id="fatigue-level" type="range" min="1" max="10" bind:value={fatigueLevel} class="slider" />
						<div class="scale-indicators">
							{#each Array(10) as _, i}
								<div class="indicator" class:active={fatigueLevel >= i + 1}></div>
							{/each}
						</div>
					</div>

					<div class="question-group">
						<label for="sleep-quality">
							<span class="label-text">{lt('Sleep quality last night', 'গত রাতের ঘুমের মান')}</span>
							<span class="label-value">{sleepQuality}/10</span>
						</label>
						<div class="scale-labels">
							<span>{lt('Poor', 'খারাপ')}</span>
							<span>{lt('Excellent', 'চমৎকার')}</span>
						</div>
						<input id="sleep-quality" type="range" min="1" max="10" bind:value={sleepQuality} class="slider" />
						<div class="scale-indicators">
							{#each Array(10) as _, i}
								<div class="indicator" class:active={sleepQuality >= i + 1}></div>
							{/each}
						</div>
					</div>

					<div class="question-group">
						<label for="readiness-level">
							<span class="label-text">{lt('How ready do you feel for cognitive tasks?', 'মানসিক কাজের জন্য আপনি কতটা প্রস্তুত?')}</span>
							<span class="label-value">{readinessLevel}/10</span>
						</label>
						<div class="scale-labels">
							<span>{lt('Not ready', 'প্রস্তুত নই')}</span>
							<span>{lt('Very ready', 'খুব প্রস্তুত')}</span>
						</div>
						<input id="readiness-level" type="range" min="1" max="10" bind:value={readinessLevel} class="slider" />
						<div class="scale-indicators">
							{#each Array(10) as _, i}
								<div class="indicator" class:active={readinessLevel >= i + 1}></div>
							{/each}
						</div>
					</div>

					<div class="question-group inline">
						<label for="medication">{lt('Medication taken today?', 'আজ ওষুধ নিয়েছেন?')}</label>
						<select id="medication" bind:value={medicationTaken} class="select-input">
							<option value={null}>{lt('Not sure', 'নিশ্চিত নই')}</option>
							<option value={true}>{lt('Yes', 'হ্যাঁ')}</option>
							<option value={false}>{lt('No', 'না')}</option>
						</select>
					</div>

					{#if medicationTaken}
						<div class="question-group inline">
							<label for="hours-since-med">{lt('Hours since last dose', 'শেষ ডোজের পর ঘণ্টা')}</label>
							<input
								id="hours-since-med"
								type="number"
								min="0"
								max="24"
								step="0.5"
								bind:value={hoursSinceMedication}
								class="number-input"
							/>
						</div>
					{/if}
				</div>
			</div>

			<div class="modal-footer">
				<button class="btn-skip" on:click={skip} disabled={submitting}>
					{lt('Skip for now', 'এখন এড়িয়ে যান')}
				</button>
				<button class="btn-submit" on:click={submitQuestionnaire} disabled={submitting}>
					{submitting ? lt('Saving...', 'সংরক্ষণ হচ্ছে...') : lt('Start training', 'ট্রেনিং শুরু করুন')}
				</button>
			</div>

			<div class="privacy-note">
				{lt('This check-in is saved once and reused across the session.', 'এই চেক-ইন একবার সংরক্ষণ হলে পুরো সেশনে ব্যবহার করা হবে।')}
			</div>
		</div>
	</div>
{/if}

<style>
	.questionnaire-overlay {
		position: fixed;
		inset: 0;
		background: rgba(15, 23, 42, 0.58);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 20px;
	}

	.questionnaire-modal {
		background: linear-gradient(160deg, #0f766e 0%, #0369a1 100%);
		border-radius: 24px;
		max-width: 620px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 28px 70px rgba(15, 23, 42, 0.4);
	}

	.modal-header,
	.modal-body,
	.modal-footer,
	.privacy-note {
		padding-left: 28px;
		padding-right: 28px;
	}

	.modal-header {
		padding-top: 28px;
		padding-bottom: 22px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.16);
	}

	.modal-header h2,
	.subtitle,
	.question-section h3,
	label,
	.privacy-note {
		margin: 0;
		color: #fff;
	}

	.modal-header h2 {
		font-size: 1.9rem;
	}

	.subtitle,
	.privacy-note {
		margin-top: 0.45rem;
		color: rgba(255, 255, 255, 0.82);
		line-height: 1.5;
	}

	.modal-body {
		padding-top: 24px;
		padding-bottom: 24px;
	}

	.question-section {
		display: grid;
		gap: 1rem;
	}

	.question-section h3 {
		font-size: 0.9rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.question-group {
		display: grid;
		gap: 0.65rem;
	}

	.question-group.inline {
		grid-template-columns: 1fr 180px;
		align-items: center;
	}

	label {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		font-size: 0.98rem;
		font-weight: 600;
	}

	.label-value {
		color: #bae6fd;
		font-weight: 800;
	}

	.scale-labels {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.72);
	}

	.slider {
		width: 100%;
		height: 8px;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.2);
		outline: none;
		-webkit-appearance: none;
		appearance: none;
	}

	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: #ffffff;
		cursor: pointer;
		box-shadow: 0 2px 12px rgba(125, 211, 252, 0.42);
	}

	.slider::-moz-range-thumb {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: #ffffff;
		cursor: pointer;
		border: none;
		box-shadow: 0 2px 12px rgba(125, 211, 252, 0.42);
	}

	.scale-indicators {
		display: flex;
		gap: 4px;
	}

	.indicator {
		flex: 1;
		height: 4px;
		background: rgba(255, 255, 255, 0.18);
		border-radius: 999px;
	}

	.indicator.active {
		background: #bae6fd;
	}

	.number-input,
	.select-input {
		padding: 0.85rem 0.95rem;
		border-radius: 14px;
		border: 1px solid rgba(255, 255, 255, 0.24);
		background: rgba(255, 255, 255, 0.12);
		color: #ffffff;
		font: inherit;
	}

	.modal-footer {
		padding-top: 18px;
		padding-bottom: 18px;
		display: flex;
		gap: 14px;
		border-top: 1px solid rgba(255, 255, 255, 0.16);
	}

	.btn-skip,
	.btn-submit {
		border: none;
		border-radius: 999px;
		padding: 0.95rem 1.1rem;
		font-weight: 800;
		cursor: pointer;
	}

	.btn-skip {
		flex: 1;
		background: rgba(255, 255, 255, 0.12);
		color: #fff;
		border: 1px solid rgba(255, 255, 255, 0.24);
	}

	.btn-submit {
		flex: 2;
		background: linear-gradient(135deg, #ffffff, #e0f2fe);
		color: #0f172a;
	}

	.btn-skip:disabled,
	.btn-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.privacy-note {
		padding-bottom: 22px;
		text-align: center;
		font-size: 0.8rem;
	}

	.error-message {
		padding: 0.9rem 1rem;
		border-radius: 14px;
		background: rgba(239, 68, 68, 0.16);
		border: 1px solid rgba(254, 202, 202, 0.32);
		color: #fee2e2;
		font-size: 0.92rem;
	}

	@media (max-width: 640px) {
		.question-group.inline {
			grid-template-columns: 1fr;
		}

		.modal-footer {
			flex-direction: column;
		}
	}
</style>
