

export const index = 56;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/landmark-task/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/56.bdrsdRBg.js"];
export const stylesheets = [];
export const fonts = [];
