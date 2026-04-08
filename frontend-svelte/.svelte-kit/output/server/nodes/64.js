

export const index = 64;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/sart/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/64.BAzkx6-3.js"];
export const stylesheets = [];
export const fonts = [];
