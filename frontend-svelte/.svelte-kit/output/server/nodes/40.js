

export const index = 40;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/progress/achievements/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/40.QGtNVFRM.js"];
export const stylesheets = [];
export const fonts = [];
