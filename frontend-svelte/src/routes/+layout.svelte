<script>
	import { dev } from '$app/environment';
	import { page } from '$app/stores';
	import { training } from '$lib/api';
	import PublicLanguageSwitcher from '$lib/components/PublicLanguageSwitcher.svelte';
	import DevPanel from '$lib/components/DevPanel.svelte';
	import { initializeLocale, localize, translateText } from '$lib/i18n';
	import { authReady, markAuthReady, user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	import '../app.css';

	let currentUser = null;
	const PUBLIC_LANGUAGE_ROUTES = new Set(['/', '/login', '/register']);
	const GAME_ROUTE_PREFIXES = ['/training', '/baseline/tasks'];
	// Keep this list in sync with `npm run audit:bangla-ui`.
	const LEGACY_GAME_ROUTES = new Set([
		'/training',
		'/training/cancellation-test',
		'/training/inspection-time',
		'/training/letter-number-sequencing',
		'/training/multiple-object-tracking',
		'/training/pattern-comparison',
		'/training/plus-minus',
		'/training/sdmt',
		'/training/stockings-of-cambridge',
		'/training/tower-of-london',
		'/training/twenty-questions',
		'/training/useful-field-of-view',
		'/training/visual-search',
		'/baseline/tasks/attention',
		'/baseline/tasks/flexibility',
		'/baseline/tasks/planning',
		'/baseline/tasks/processing-speed',
		'/baseline/tasks/visual-scanning'
	]);
	const NATIVE_LOCALIZED_ROUTES = new Set([
		'/baseline/tasks/working-memory',
		'/training/category-fluency',
		'/training/dccs',
		'/training/digit-span',
		'/training/dual-n-back',
		'/training/flanker',
		'/training/gonogo',
		'/training/operation-span',
		'/training/pasat',
		'/training/spatial-span',
		'/training/stroop',
		'/training/trail-making-a',
		'/training/trail-making-b',
		'/training/verbal-fluency',
		'/training/wcst'
	]);

	const unsubscribe = user.subscribe((value) => {
		currentUser = value;
	});

	onMount(() => {
		if (typeof window === 'undefined') return;

		initializeLocale();
		markAuthReady();

		const originalFetch = window.fetch.bind(window);
		const originalAlert = window.alert.bind(window);
		const originalConfirm = window.confirm.bind(window);
		const originalPrompt = window.prompt.bind(window);
		const submitUrlPattern = /\/api\/training\/tasks\/[^/]+\/submit\//i;

		window.fetch = async (input, init) => {
			const response = await originalFetch(input, init);

			try {
				const requestUrl = typeof input === 'string'
					? input
					: input instanceof Request
						? input.url
						: String(input);

				if (response.ok && submitUrlPattern.test(requestUrl)) {
					const contextId = Number.parseInt(new URL(window.location.href).searchParams.get('contextId') || '', 10);

					if (Number.isInteger(contextId) && contextId > 0) {
						const contentType = response.headers.get('content-type') || '';

						if (contentType.includes('application/json')) {
							const payload = await response.clone().json();
							const sessionId = payload?.session_id ?? payload?.id;

							if (sessionId) {
								await training.linkContextToSession(sessionId, contextId);
							}
						}
					}
				}
			} catch (error) {
				console.error('Failed to auto-link questionnaire context after task submission:', error);
			}

			return response;
		};

		window.alert = (message) => originalAlert(translateText(message));
		window.confirm = (message) => originalConfirm(translateText(message));
		window.prompt = (message, defaultValue = '') => originalPrompt(translateText(message), defaultValue);

		return () => {
			window.fetch = originalFetch;
			window.alert = originalAlert;
			window.confirm = originalConfirm;
			window.prompt = originalPrompt;
			unsubscribe();
		};
	});

	$: showPublicLanguageSwitcher =
		$authReady && !currentUser && PUBLIC_LANGUAGE_ROUTES.has($page.url.pathname);
	$: isGameRoute = GAME_ROUTE_PREFIXES.some((prefix) =>
		$page.url.pathname === prefix || $page.url.pathname.startsWith(`${prefix}/`)
	);
	$: useLegacyDomLocalization = isGameRoute
		? LEGACY_GAME_ROUTES.has($page.url.pathname)
		: !NATIVE_LOCALIZED_ROUTES.has($page.url.pathname);
</script>

{#if showPublicLanguageSwitcher}
	<PublicLanguageSwitcher />
{/if}

{#if useLegacyDomLocalization}
	<div class="app-localization-root" use:localize>
		<slot />
	</div>
{:else}
	<div class="app-localization-root">
		<slot />
	</div>
{/if}

<!-- Dev Tools Panel (only shows in development) -->
{#if dev}
	<DevPanel />
{/if}

<style>
	.app-localization-root {
		display: contents;
	}
</style>
