<script>
	import { dev } from '$app/environment';
	import { goto } from '$app/navigation';
	import DevPanel from '$lib/components/DevPanel.svelte';
	import { locale, localeText, locale as activeLocale, uiText } from '$lib/i18n';
	import { onMount } from 'svelte';

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	onMount(() => {
		if (!dev) {
			goto('/dashboard');
		}
	});
</script>

{#if dev}
	<div class="dev-games-page">
		<section class="dev-shell">
			<p class="eyebrow">{uiText("NeuroBloom Dev", $activeLocale)}</p>
			<h1>{lt('Game Development Workspace', 'গেম ডেভেলপমেন্ট ওয়ার্কস্পেস')}</h1>
			<p class="copy">
				{lt(
					'This page is isolated from the regular patient journey. Use it only to inspect and launch games during development.',
					'এই পেজটি নিয়মিত রোগীর যাত্রা থেকে আলাদা রাখা হয়েছে। উন্নয়নের সময় শুধু গেম দেখা ও চালুর জন্য এটি ব্যবহার করুন।'
				)}
			</p>
			<div class="actions">
				<a class="ghost-link" href="/dashboard">{lt('Back to dashboard', 'ড্যাশবোর্ডে ফিরুন')}</a>
			</div>
		</section>
	</div>

	<DevPanel />
{/if}

<style>
	.dev-games-page {
		padding: 1.5rem;
	}

	.dev-shell {
		max-width: 960px;
		margin: 0 auto;
		padding: 1.5rem;
		border-radius: 24px;
		background: rgba(248, 250, 252, 0.92);
		border: 1px solid rgba(226, 232, 240, 0.9);
		box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
	}

	.eyebrow {
		margin: 0;
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #7c3aed;
	}

	h1 {
		margin: 0.35rem 0 0.75rem;
		font-size: clamp(2rem, 3vw, 2.8rem);
		color: #111827;
	}

	.copy {
		margin: 0;
		max-width: 60ch;
		line-height: 1.65;
		color: #475569;
	}

	.actions {
		margin-top: 1rem;
	}

	.ghost-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.8rem 1.1rem;
		border-radius: 999px;
		font-weight: 700;
		text-decoration: none;
		background: rgba(124, 58, 237, 0.08);
		color: #6d28d9;
	}
 </style>
