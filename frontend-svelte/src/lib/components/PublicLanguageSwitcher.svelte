<script>
	import { locale, setLocale } from '$lib/i18n';

	function chooseLanguage(nextLocale) {
		setLocale(nextLocale, { syncUser: false });
	}
</script>

<div class="language-switcher" aria-label="Language switcher" data-localize-skip>
	<button
		type="button"
		class:active={$locale === 'en'}
		on:click={() => chooseLanguage('en')}
	>
		EN
	</button>
	<button
		type="button"
		class:active={$locale === 'bn'}
		on:click={() => chooseLanguage('bn')}
	>
		বাং
	</button>
</div>

<style>
	.language-switcher {
		position: fixed;
		top: 1rem;
		right: 1rem;
		z-index: 1100;
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.35rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.82);
		backdrop-filter: blur(14px);
		border: 1px solid rgba(148, 163, 184, 0.24);
		box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
	}

	button {
		border: none;
		border-radius: 999px;
		padding: 0.55rem 0.9rem;
		background: transparent;
		color: #475569;
		font-size: 0.82rem;
		font-weight: 800;
		letter-spacing: 0.04em;
		cursor: pointer;
		transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
	}

	button.active {
		background: linear-gradient(135deg, #0f766e, #0f4c81);
		color: #ffffff;
		box-shadow: 0 10px 22px rgba(15, 76, 129, 0.22);
	}

	button:hover {
		transform: translateY(-1px);
	}

	@media (max-width: 640px) {
		.language-switcher {
			top: 0.75rem;
			right: 0.75rem;
		}
	}
</style>
