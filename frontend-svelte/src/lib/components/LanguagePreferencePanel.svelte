<script>
	import { locale, setLocale } from '$lib/i18n';

	export let title = 'Language Preference';
	export let description =
		'Choose the language used across the NeuroBloom interface, training instructions, and visible numbers.';
	export let compact = false;

	function handleChange(event) {
		setLocale(event.currentTarget.value);
	}
</script>

<section class:compact class="language-panel">
	<div class="language-copy">
		<p class="language-kicker">Preferences</p>
		<h3>{title}</h3>
		<p>{description}</p>
	</div>

	<label class="language-field">
		<span>Interface language</span>
		<select data-localize-skip value={$locale} on:change={handleChange}>
			<option value="en">English</option>
			<option value="bn">বাংলা</option>
		</select>
	</label>
</section>

<style>
	.language-panel {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1.25rem;
		padding: 1.15rem 1.25rem;
		border-radius: 18px;
		background: linear-gradient(135deg, rgba(15, 118, 110, 0.08), rgba(14, 116, 144, 0.08));
		border: 1px solid rgba(15, 118, 110, 0.14);
	}

	.language-panel.compact {
		padding: 1rem 1.1rem;
	}

	.language-copy h3,
	.language-copy p,
	.language-kicker {
		margin: 0;
	}

	.language-copy h3 {
		margin-top: 0.2rem;
		font-size: 1.05rem;
		color: #0f172a;
	}

	.language-copy p:last-child {
		margin-top: 0.45rem;
		max-width: 36rem;
		color: #475569;
		line-height: 1.55;
	}

	.language-kicker {
		font-size: 0.76rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #0f766e;
	}

	.language-field {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		min-width: 190px;
		font-size: 0.84rem;
		font-weight: 700;
		color: #0f172a;
	}

	select {
		border: 1px solid rgba(15, 118, 110, 0.2);
		border-radius: 12px;
		padding: 0.8rem 0.95rem;
		background: rgba(255, 255, 255, 0.92);
		color: #0f172a;
		font-size: 0.95rem;
		font-weight: 700;
		outline: none;
	}

	select:focus {
		border-color: rgba(14, 116, 144, 0.48);
		box-shadow: 0 0 0 4px rgba(14, 116, 144, 0.12);
	}

	@media (max-width: 720px) {
		.language-panel {
			flex-direction: column;
			align-items: stretch;
		}

		.language-field {
			min-width: 0;
		}
	}
</style>
