<script>
	import DevPanel from '$lib/components/DevPanel.svelte';
	import '../app.css';
</script>

<slot />

<!-- Dev Tools Panel (only shows in development) -->
<DevPanel />
