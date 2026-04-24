<script>
	import { goto } from '$app/navigation';
	import { locale, localeText, setLocale } from '$lib/i18n/runtime.js';
	import { user } from '$lib/stores';

	let currentUser = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	function continueToDashboard() {
		goto('/dashboard');
	}

	const copy = {
		banglaShort: { en: 'BN', bn: 'বাংলা' },
		backgroundAlt: { en: 'NeuroBloom background', bn: 'NeuroBloom পটভূমি' },
		badge: { en: 'Clinically Validated · MS Cognitive Care', bn: 'ক্লিনিক্যালভাবে যাচাইকৃত · MS কগনিটিভ কেয়ার' },
		subtitle: {
			en: 'A professional platform for cognitive rehabilitation, patient monitoring, and multiple sclerosis support.',
			bn: 'কগনিটিভ পুনর্বাসন, রোগী পর্যবেক্ষণ এবং মাল্টিপল স্ক্লেরোসিস সহায়তার জন্য পেশাদার প্ল্যাটফর্ম।'
		},
		training: { en: 'Adaptive cognitive training', bn: 'অভিযোজিত কগনিটিভ ট্রেনিং' },
		progress: { en: 'Progress monitoring', bn: 'অগ্রগতি পর্যবেক্ষণ' },
		workflows: { en: 'MS-focused care workflows', bn: 'MS-কেন্দ্রিক কেয়ার ওয়ার্কফ্লো' },
		welcome: { en: 'Welcome', bn: 'স্বাগতম' },
		secureAccess: {
			en: 'Secure access to your NeuroBloom workspace',
			bn: 'আপনার NeuroBloom ওয়ার্কস্পেসে নিরাপদ প্রবেশ'
		},
		continue: { en: 'Continue to Dashboard', bn: 'ড্যাশবোর্ডে যান' },
		switchAccount: { en: 'Switch account', bn: 'অন্য অ্যাকাউন্ট ব্যবহার করুন' },
		signIn: { en: 'Sign In', bn: 'সাইন ইন' },
		createAccount: { en: 'Create Account', bn: 'অ্যাকাউন্ট তৈরি করুন' },
		note: {
			en: 'Built for a calm, clear, and patient-friendly experience.',
			bn: 'শান্ত, পরিষ্কার ও রোগীবান্ধব ব্যবহারের অভিজ্ঞতার জন্য তৈরি।'
		}
	};

	$: welcomeMessage = currentUser
		? localeText(
				{
					en: `Welcome back, ${currentUser.email}!`,
					bn: `আবার স্বাগতম, ${currentUser.email}!`
				},
				$locale
			)
		: '';
</script>

<div class="page-shell">
	<div class="language-switcher">
		<button class:active={$locale === 'en'} on:click={() => setLocale('en')}>EN</button>
		<button class:active={$locale === 'bn'} on:click={() => setLocale('bn')}>{localeText(copy.banglaShort, $locale)}</button>
	</div>

	<div class="page-grid">
		<section class="visual-panel">
			<div class="visual-overlay"></div>
			<img src="/background.png" alt={localeText(copy.backgroundAlt, $locale)} class="visual-image" />

			<div class="visual-content">
				<div class="brand-badge">{localeText(copy.badge, $locale)}</div>

				<h1>NeuroBloom</h1>

				<p class="visual-subtitle">
					{localeText(copy.subtitle, $locale)}
				</p>

				<div class="info-list">
					<div>{localeText(copy.training, $locale)}</div>
					<div>{localeText(copy.progress, $locale)}</div>
					<div>{localeText(copy.workflows, $locale)}</div>
				</div>
			</div>
		</section>

		<section class="auth-panel">
			<div class="auth-card">
				<div class="auth-header">
					<h2>{localeText(copy.welcome, $locale)}</h2>
					<p>{localeText(copy.secureAccess, $locale)}</p>
				</div>

				{#if currentUser}
					<div class="welcome-block">
						<div class="welcome-avatar">
							{currentUser.email?.charAt(0).toUpperCase() ?? 'U'}
						</div>

						<p class="welcome-msg">{welcomeMessage}</p>

						<button class="primary-btn" on:click={continueToDashboard}>
							{localeText(copy.continue, $locale)}
						</button>

						<a href="/login?reset=1" class="text-link">{localeText(copy.switchAccount, $locale)}</a>
					</div>
				{:else}
					<div class="action-block">
						<a href="/login" class="primary-btn">{localeText(copy.signIn, $locale)}</a>
						<a href="/register" class="secondary-btn">{localeText(copy.createAccount, $locale)}</a>
					</div>
				{/if}

				<div class="bottom-note">
					<p>{localeText(copy.note, $locale)}</p>
				</div>
			</div>
		</section>
	</div>
</div>

<style>
	:global(html, body) {
		margin: 0;
		padding: 0;
		min-height: 100%;
		font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	:global(body) {
		overflow-x: hidden;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.page-shell {
		min-height: 100vh;
		position: relative;
		background:
			radial-gradient(circle at top left, rgba(53, 115, 255, 0.1), transparent 28%),
			radial-gradient(circle at bottom right, rgba(126, 92, 255, 0.08), transparent 28%),
			linear-gradient(135deg, #07111f 0%, #09162a 45%, #06101d 100%);
	}

	.language-switcher {
		position: absolute;
		top: 1.25rem;
		right: 1.25rem;
		z-index: 20;
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.35rem;
		background: rgba(255, 255, 255, 0.12);
		border: 1px solid rgba(255, 255, 255, 0.14);
		border-radius: 999px;
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
	}

	.language-switcher button {
		border: none;
		background: transparent;
		color: rgba(255, 255, 255, 0.78);
		padding: 0.55rem 0.85rem;
		border-radius: 999px;
		font-size: 0.78rem;
		font-weight: 700;
		cursor: pointer;
		transition: 0.2s ease;
	}

	.language-switcher button.active {
		background: #0c7ea7;
		color: white;
	}

	.page-grid {
		min-height: 100vh;
		display: grid;
		grid-template-columns: 1fr 0.9fr;
	}

	.visual-panel {
		position: relative;
		overflow: hidden;
		display: flex;
		align-items: center;
		padding: 3rem 3.5rem;
		border-right: 1px solid rgba(255, 255, 255, 0.04);
	}

	.visual-image {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: contain;
		object-position: center;
		opacity: 0.55;
		filter: saturate(1.05) contrast(1.05);
		pointer-events: none;
		user-select: none;
	}

	.visual-overlay {
		position: absolute;
		inset: 0;
		background:
			linear-gradient(to right, rgba(7, 17, 31, 0.28), rgba(7, 17, 31, 0.52)),
			linear-gradient(to top, rgba(7, 17, 31, 0.58), rgba(7, 17, 31, 0.1));
		z-index: 1;
	}

	.visual-content {
		position: relative;
		z-index: 2;
		max-width: 460px;
	}

	.brand-badge {
		display: inline-block;
		padding: 0.5rem 0.95rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.08);
		border: 1px solid rgba(255, 255, 255, 0.14);
		font-size: 0.76rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.86);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		margin-bottom: 1.2rem;
	}

	.visual-content h1 {
		margin: 0;
		font-size: 3.5rem;
		line-height: 1.02;
		font-weight: 800;
		letter-spacing: -0.04em;
		color: white;
	}

	.visual-subtitle {
		margin: 1rem 0 0;
		font-size: 1.02rem;
		line-height: 1.7;
		color: rgba(255, 255, 255, 0.8);
	}

	.info-list {
		margin-top: 1.7rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.info-list div {
		padding: 0.62rem 0.9rem;
		border-radius: 10px;
		background: rgba(255, 255, 255, 0.07);
		border: 1px solid rgba(255, 255, 255, 0.1);
		color: rgba(255, 255, 255, 0.84);
		font-size: 0.84rem;
		font-weight: 500;
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
	}

	.auth-panel {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.auth-card {
		width: 100%;
		max-width: 480px;
		padding: 2.4rem;
		border-radius: 26px;
		background: rgba(255, 255, 255, 0.06);
		border: 1px solid rgba(255, 255, 255, 0.1);
		box-shadow: 0 24px 60px rgba(0, 0, 0, 0.34);
		backdrop-filter: blur(18px);
		-webkit-backdrop-filter: blur(18px);
	}

	.auth-header h2 {
		margin: 0;
		color: white;
		font-size: 2.2rem;
		font-weight: 800;
		letter-spacing: -0.02em;
	}

	.auth-header p {
		margin: 0.65rem 0 0;
		color: rgba(255, 255, 255, 0.68);
		font-size: 0.96rem;
		line-height: 1.6;
	}

	.action-block,
	.welcome-block {
		margin-top: 1.8rem;
		display: flex;
		flex-direction: column;
		gap: 0.95rem;
	}

	.primary-btn,
	.secondary-btn {
		width: 100%;
		min-height: 54px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 14px;
		text-decoration: none;
		font-size: 1rem;
		font-weight: 700;
		transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
	}

	.primary-btn {
		background: white;
		color: #0d1b2d;
		border: none;
		cursor: pointer;
		box-shadow: 0 8px 24px rgba(255, 255, 255, 0.07);
	}

	.primary-btn:hover {
		transform: translateY(-1px);
		box-shadow: 0 12px 28px rgba(255, 255, 255, 0.1);
	}

	.secondary-btn {
		background: transparent;
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.16);
	}

	.secondary-btn:hover {
		transform: translateY(-1px);
		background: rgba(255, 255, 255, 0.05);
	}

	.welcome-avatar {
		width: 58px;
		height: 58px;
		border-radius: 50%;
		background: white;
		color: #0d1b2d;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.35rem;
		font-weight: 800;
		margin: 0 auto 0.25rem;
	}

	.welcome-msg {
		margin: 0;
		text-align: center;
		color: rgba(255, 255, 255, 0.88);
		font-size: 0.96rem;
		line-height: 1.6;
	}

	.text-link {
		text-align: center;
		color: rgba(255, 255, 255, 0.62);
		text-decoration: none;
		font-size: 0.88rem;
	}

	.text-link:hover {
		color: rgba(255, 255, 255, 0.85);
	}

	.bottom-note {
		margin-top: 1.5rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.08);
	}

	.bottom-note p {
		margin: 0;
		color: rgba(255, 255, 255, 0.54);
		font-size: 0.84rem;
		line-height: 1.6;
	}

	@media (max-width: 980px) {
		.page-grid {
			grid-template-columns: 1fr;
		}

		.visual-panel {
			min-height: 44vh;
			padding: 2.2rem 1.4rem;
			align-items: flex-end;
			border-right: none;
			border-bottom: 1px solid rgba(255, 255, 255, 0.04);
		}

		.visual-content {
			max-width: 100%;
		}

		.visual-content h1 {
			font-size: 2.8rem;
		}

		.visual-image {
			object-position: center;
			opacity: 0.42;
		}

		.auth-panel {
			padding: 1.25rem;
		}

		.auth-card {
			max-width: 100%;
		}
	}

	@media (max-width: 640px) {
		.language-switcher {
			top: 0.9rem;
			right: 0.9rem;
		}

		.visual-panel {
			min-height: 38vh;
			padding: 1.5rem 1rem;
		}

		.visual-content h1 {
			font-size: 2.3rem;
		}

		.visual-subtitle {
			font-size: 0.94rem;
			line-height: 1.6;
		}

		.info-list {
			gap: 0.55rem;
		}

		.info-list div {
			font-size: 0.8rem;
			padding: 0.58rem 0.75rem;
		}

		.auth-panel {
			padding: 1rem;
		}

		.auth-card {
			padding: 1.5rem;
			border-radius: 20px;
		}

		.auth-header h2 {
			font-size: 1.8rem;
		}
	}
</style>
