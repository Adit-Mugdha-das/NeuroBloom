

export const index = 20;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/baseline/tasks/visual-scanning/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/20.o7_jfbWO.js"];
export const stylesheets = [];
export const fonts = [];
