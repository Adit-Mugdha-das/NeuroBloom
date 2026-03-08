<script>
	import { training } from '$lib/api';
	import DevPanel from '$lib/components/DevPanel.svelte';
	import { onMount } from 'svelte';
	import '../app.css';

	onMount(() => {
		if (typeof window === 'undefined') return;

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
		};
	});
</script>

<slot />

<!-- Dev Tools Panel (only shows in development) -->
<DevPanel />
