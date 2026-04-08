

export const index = 15;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/baseline/results/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/15.Cizi5YxF.js"];
export const stylesheets = [];
export const fonts = [];
