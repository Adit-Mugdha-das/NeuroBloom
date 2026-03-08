<script>
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Props
	export let showQuestionnaire = true;

	// Form state
	let fatigueLevel = 5;
	let sleepQuality = 5;
	let medicationTaken = null;
	let hoursSinceMedication = null;
	let readinessLevel = 7;

	// UI state
	let submitting = false;
	let error = '';

	// Get current user
	let currentUser;
	user.subscribe(value => {
		currentUser = value;
	});

	async function submitQuestionnaire() {
		submitting = true;
		error = '';

		try {
			const response = await api.post('/api/training/session-context', {
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

			// Emit event with context_id
			dispatch('complete', {
				contextId: response.data.context_id,
				timeOfDay: response.data.time_of_day
			});

			showQuestionnaire = false;
		} catch (err) {
			error = 'Failed to save responses. Please try again.';
			console.error(err);
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
				<h2>📋 Quick Check-In</h2>
				<p class="subtitle">4 quick answers before this 4-task training session</p>
			</div>

			<div class="modal-body">
				{#if error}
					<div class="error-message">{error}</div>
				{/if}

				<!-- Essential Questions -->
				<div class="question-section">
					<h3>Session Readiness</h3>

					<!-- Fatigue Level -->
					<div class="question-group">
						<label for="fatigue-level">
							<span class="label-text">Energy Level</span>
							<span class="label-value">{fatigueLevel}/10</span>
						</label>
						<div class="scale-labels">
							<span>Exhausted</span>
							<span>Energized</span>
						</div>
						<input id="fatigue-level" type="range" min="1" max="10" bind:value={fatigueLevel} class="slider" />
						<div class="scale-indicators">
							{#each Array(10) as _, i}
								<div class="indicator" class:active={fatigueLevel >= i + 1}></div>
							{/each}
						</div>
					</div>

					<!-- Sleep Quality -->
					<div class="question-group">
						<label for="sleep-quality">
							<span class="label-text">Sleep Quality (last night)</span>
							<span class="label-value">{sleepQuality}/10</span>
						</label>
						<div class="scale-labels">
							<span>Terrible</span>
							<span>Excellent</span>
						</div>
						<input id="sleep-quality" type="range" min="1" max="10" bind:value={sleepQuality} class="slider" />
						<div class="scale-indicators">
							{#each Array(10) as _, i}
								<div class="indicator" class:active={sleepQuality >= i + 1}></div>
							{/each}
						</div>
					</div>

					<!-- Readiness -->
					<div class="question-group">
						<label for="readiness-level">
							<span class="label-text">Feeling Ready for Cognitive Tasks?</span>
							<span class="label-value">{readinessLevel}/10</span>
						</label>
						<div class="scale-labels">
							<span>Not Ready</span>
							<span>Very Ready</span>
						</div>
						<input id="readiness-level" type="range" min="1" max="10" bind:value={readinessLevel} class="slider" />
						<div class="scale-indicators">
							{#each Array(10) as _, i}
								<div class="indicator" class:active={readinessLevel >= i + 1}></div>
							{/each}
						</div>
					</div>

					<div class="question-group inline">
						<label for="medication">Medication taken today?</label>
						<select id="medication" bind:value={medicationTaken} class="select-input">
							<option value={null}>Not sure</option>
							<option value={true}>Yes</option>
							<option value={false}>No</option>
						</select>
					</div>

					{#if medicationTaken}
						<div class="question-group inline">
							<label for="hours-since-med">Hours since last dose</label>
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
					Skip for Now
				</button>
				<button class="btn-submit" on:click={submitQuestionnaire} disabled={submitting}>
					{submitting ? 'Saving...' : 'Start Training →'}
				</button>
			</div>

			<div class="privacy-note">
				🔒 This check-in is saved once and reused across the full 4-task session.
			</div>
		</div>
	</div>
{/if}

<style>
	.questionnaire-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 20px;
	}

	.questionnaire-modal {
		background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
		border-radius: 20px;
		max-width: 600px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
	}

	.modal-header {
		background: rgba(255, 255, 255, 0.1);
		padding: 30px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}

	.modal-header h2 {
		margin: 0 0 10px 0;
		color: white;
		font-size: 28px;
	}

	.subtitle {
		margin: 0;
		color: rgba(255, 255, 255, 0.8);
		font-size: 14px;
	}

	.modal-body {
		padding: 30px;
	}

	.question-section {
		margin-bottom: 20px;
	}

	.question-section h3 {
		color: white;
		font-size: 16px;
		margin-bottom: 20px;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.question-group {
		margin-bottom: 25px;
	}

	.question-group.inline {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.question-group.inline label {
		flex: 1;
		margin-bottom: 0;
	}

	label {
		display: flex;
		justify-content: space-between;
		color: white;
		font-size: 15px;
		font-weight: 500;
		margin-bottom: 10px;
	}

	.label-text {
		flex: 1;
	}

	.label-value {
		color: #4fc3f7;
		font-weight: bold;
		font-size: 16px;
	}

	.scale-labels {
		display: flex;
		justify-content: space-between;
		font-size: 12px;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 8px;
	}

	.slider {
		width: 100%;
		height: 8px;
		border-radius: 5px;
		background: rgba(255, 255, 255, 0.2);
		outline: none;
		-webkit-appearance: none;
		appearance: none;
		margin-bottom: 10px;
	}

	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #4fc3f7;
		cursor: pointer;
		box-shadow: 0 2px 10px rgba(79, 195, 247, 0.5);
	}

	.slider::-moz-range-thumb {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #4fc3f7;
		cursor: pointer;
		border: none;
		box-shadow: 0 2px 10px rgba(79, 195, 247, 0.5);
	}

	.scale-indicators {
		display: flex;
		gap: 4px;
	}

	.indicator {
		flex: 1;
		height: 4px;
		background: rgba(255, 255, 255, 0.2);
		border-radius: 2px;
		transition: background 0.2s;
	}

	.indicator.active {
		background: #4fc3f7;
	}

	.number-input,
	.select-input {
		padding: 10px 15px;
		border-radius: 8px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		background: rgba(255, 255, 255, 0.1);
		color: white;
		font-size: 15px;
		min-width: 120px;
	}

	.number-input:focus,
	.select-input:focus {
		outline: none;
		border-color: #4fc3f7;
	}

	.modal-footer {
		padding: 20px 30px;
		display: flex;
		gap: 15px;
		border-top: 1px solid rgba(255, 255, 255, 0.2);
	}

	.btn-skip {
		flex: 1;
		padding: 15px 25px;
		background: rgba(255, 255, 255, 0.1);
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-radius: 10px;
		color: white;
		font-size: 16px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-skip:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.15);
		transform: translateY(-2px);
	}

	.btn-submit {
		flex: 2;
		padding: 15px 25px;
		background: linear-gradient(135deg, #4fc3f7 0%, #2196f3 100%);
		border: none;
		border-radius: 10px;
		color: white;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-submit:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 5px 20px rgba(79, 195, 247, 0.4);
	}

	.btn-skip:disabled,
	.btn-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.privacy-note {
		padding: 15px 30px 20px;
		text-align: center;
		font-size: 12px;
		color: rgba(255, 255, 255, 0.6);
	}

	.error-message {
		padding: 12px;
		background: rgba(244, 67, 54, 0.2);
		border: 1px solid rgba(244, 67, 54, 0.5);
		border-radius: 8px;
		color: #ff5252;
		margin-bottom: 20px;
		font-size: 14px;
	}

	/* Scrollbar styling */
	.questionnaire-modal::-webkit-scrollbar {
		width: 8px;
	}

	.questionnaire-modal::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 10px;
	}

	.questionnaire-modal::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.3);
		border-radius: 10px;
	}

	.questionnaire-modal::-webkit-scrollbar-thumb:hover {
		background: rgba(255, 255, 255, 0.4);
	}
</style>
