

export const index = 60;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/pasat/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/60.hhOJHxb6.js"];
export const stylesheets = [];
export const fonts = [];
