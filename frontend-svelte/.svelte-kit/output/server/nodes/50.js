

export const index = 50;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/dccs/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/50.BwBOCr0p.js"];
export const stylesheets = [];
export const fonts = [];
