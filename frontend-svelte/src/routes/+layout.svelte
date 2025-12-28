<script>
	import '../app.css';
	import DevPanel from '$lib/components/DevPanel.svelte';
</script>

<slot />

<!-- Dev Tools Panel (only shows in development) -->
<DevPanel />
