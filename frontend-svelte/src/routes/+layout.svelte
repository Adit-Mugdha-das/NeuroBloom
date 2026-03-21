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
	const NATIVE_LOCALIZED_ROUTES = new Set([
		'/baseline/tasks/working-memory',
		'/training/category-fluency',
		'/training/operation-span',
		'/training/pasat',
		'/training/verbal-fluency'
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
	$: useLegacyDomLocalization = !NATIVE_LOCALIZED_ROUTES.has($page.url.pathname);
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
