

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/progress/_layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/2.C2f8hCgh.js"];
export const stylesheets = [];
export const fonts = [];
