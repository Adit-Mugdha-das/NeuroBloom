

export const index = 38;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/prescriptions/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/38.uXFhTD2I.js"];
export const stylesheets = [];
export const fonts = [];
