

export const index = 53;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/flanker/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/53.CVZ2tcEM.js"];
export const stylesheets = [];
export const fonts = [];
