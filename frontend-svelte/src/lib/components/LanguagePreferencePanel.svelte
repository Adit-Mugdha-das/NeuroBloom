<script>
	import { locale, localeText, setLocale } from '$lib/i18n/runtime.js';

	export let title = {
		en: 'Language Preference',
		bn: 'ভাষা পছন্দ'
	};
	export let description = {
		en: 'Choose the language used across the NeuroBloom interface, training instructions, and visible numbers.',
		bn: 'NeuroBloom ইন্টারফেস, ট্রেনিং নির্দেশনা এবং দৃশ্যমান সংখ্যায় কোন ভাষা ব্যবহার হবে তা বেছে নিন।'
	};
	export let compact = false;

	const panelCopy = {
		'Language Preference': { en: 'Language Preference', bn: 'ভাষা পছন্দ' },
		'Choose the language used across the NeuroBloom interface, training instructions, and visible numbers.': {
			en: 'Choose the language used across the NeuroBloom interface, training instructions, and visible numbers.',
			bn: 'NeuroBloom ইন্টারফেস, ট্রেনিং নির্দেশনা এবং দৃশ্যমান সংখ্যায় কোন ভাষা ব্যবহার হবে তা বেছে নিন।'
		},
		'Choose the admin workspace language for navigation, system dashboards, and visible metrics.': {
			en: 'Choose the admin workspace language for navigation, system dashboards, and visible metrics.',
			bn: 'অ্যাডমিন নেভিগেশন, সিস্টেম ড্যাশবোর্ড এবং দৃশ্যমান মেট্রিকের ভাষা বেছে নিন।'
		},
		'Set the clinician workspace language for dashboards, notifications, and task-facing copy.': {
			en: 'Set the clinician workspace language for dashboards, notifications, and task-facing copy.',
			bn: 'ড্যাশবোর্ড, নোটিফিকেশন এবং টাস্ক-সংক্রান্ত লেখার জন্য ক্লিনিশিয়ান ওয়ার্কস্পেসের ভাষা ঠিক করুন।'
		}
	};

	function panelText(value) {
		return localeText(typeof value === 'string' ? panelCopy[value] ?? value : value, $locale);
	}

	$: panelTitle = panelText(title);
	$: panelDescription = panelText(description);

	function handleChange(event) {
		setLocale(event.currentTarget.value);
	}
</script>

<section class:compact class="language-panel">
	<div class="language-copy">
		<p class="language-kicker">{localeText({ en: 'Preferences', bn: 'পছন্দ' }, $locale)}</p>
		<h3>{panelTitle}</h3>
		<p>{panelDescription}</p>
	</div>

	<label class="language-field">
		<span>{localeText({ en: 'Interface language', bn: 'ইন্টারফেসের ভাষা' }, $locale)}</span>
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
