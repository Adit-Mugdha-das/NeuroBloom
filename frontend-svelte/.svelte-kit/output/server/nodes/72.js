

export const index = 72;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/twenty-questions/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/72.Di-0RrWF.js"];
export const stylesheets = [];
export const fonts = [];
