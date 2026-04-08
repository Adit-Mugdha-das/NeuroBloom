

export const index = 75;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/visual-search/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/75.B4KRWx5C.js"];
export const stylesheets = [];
export const fonts = [];
