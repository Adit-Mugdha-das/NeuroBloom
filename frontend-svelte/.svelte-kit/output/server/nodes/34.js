

export const index = 34;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/find-doctor/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/34.DE6nV-o7.js"];
export const stylesheets = [];
export const fonts = [];
