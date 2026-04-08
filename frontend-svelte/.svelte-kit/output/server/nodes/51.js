

export const index = 51;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/digit-span/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/51.Dv0rU7xK.js"];
export const stylesheets = [];
export const fonts = [];
