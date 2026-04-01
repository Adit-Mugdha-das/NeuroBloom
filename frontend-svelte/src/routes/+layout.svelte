<script>
	import { afterNavigate } from '$app/navigation';
	import { dev } from '$app/environment';
	import { page } from '$app/stores';
	import { training } from '$lib/api';
	import PublicLanguageSwitcher from '$lib/components/PublicLanguageSwitcher.svelte';
	import DevPanel from '$lib/components/DevPanel.svelte';
	import {
		initializeLocale,
		localize,
		queueLocalizationRefresh,
		translateText
	} from '$lib/i18n';
	import {
		getRouteLocalizationMode,
		PUBLIC_LANGUAGE_ROUTES,
	} from '$lib/i18n/route-localization.js';
	import { authReady, markAuthReady, user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	import '../app.css';

	let currentUser = null;

	const unsubscribe = user.subscribe((value) => {
		currentUser = value;
	});

	afterNavigate(() => {
		queueLocalizationRefresh('full');
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

			queueLocalizationRefresh('pulse');

			return response;
		};

		window.alert = (message) => originalAlert(translateText(message));
		window.confirm = (message) => originalConfirm(translateText(message));
		window.prompt = (message, defaultValue = '') => originalPrompt(translateText(message), defaultValue);

		const interactionEvents = ['click', 'change', 'submit'];
		const handleInteraction = () => {
			if (getRouteLocalizationMode(window.location.pathname) === 'refresh') {
				queueLocalizationRefresh('pulse');
			}
		};

		for (const eventName of interactionEvents) {
			window.document.addEventListener(eventName, handleInteraction, true);
		}

		return () => {
			window.fetch = originalFetch;
			window.alert = originalAlert;
			window.confirm = originalConfirm;
			window.prompt = originalPrompt;
			for (const eventName of interactionEvents) {
				window.document.removeEventListener(eventName, handleInteraction, true);
			}
			unsubscribe();
		};
	});

	$: showPublicLanguageSwitcher =
		$authReady && !currentUser && PUBLIC_LANGUAGE_ROUTES.has($page.url.pathname);
	$: localizationMode = getRouteLocalizationMode($page.url.pathname);
</script>

{#if showPublicLanguageSwitcher}
	<PublicLanguageSwitcher />
{/if}

{#if localizationMode !== 'native'}
	<div class="app-localization-root" use:localize={localizationMode}>
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
