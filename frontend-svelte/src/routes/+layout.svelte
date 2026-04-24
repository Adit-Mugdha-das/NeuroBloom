<script>
	import { page } from '$app/stores';
	import { training } from '$lib/api';
	import PublicLanguageSwitcher from '$lib/components/PublicLanguageSwitcher.svelte';
	import { initializeLocale } from '$lib/i18n/runtime.js';
	import { PUBLIC_LANGUAGE_ROUTES } from '$lib/i18n/route-localization.js';
	import { authReady, markAuthReady, user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	import '../app.css';

	let currentUser = null;

	const unsubscribe = user.subscribe((value) => {
		currentUser = value;
	});

	onMount(() => {
		if (typeof window === 'undefined') return;

		initializeLocale();
		markAuthReady();

		const originalFetch = window.fetch.bind(window);
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

		return () => {
			window.fetch = originalFetch;
			unsubscribe();
		};
	});

	$: showPublicLanguageSwitcher =
		$authReady && !currentUser && PUBLIC_LANGUAGE_ROUTES.has($page.url.pathname);
</script>

{#if showPublicLanguageSwitcher}
	<PublicLanguageSwitcher />
{/if}

<div class="app-localization-root">
	<slot />
</div>

<style>
	.app-localization-root {
		display: contents;
	}
</style>
