

export const index = 45;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/settings/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/45.ICsbWRQl.js"];
export const stylesheets = [];
export const fonts = [];
