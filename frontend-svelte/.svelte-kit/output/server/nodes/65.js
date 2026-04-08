

export const index = 65;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/training/sdmt/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/65.DNpoQgmx.js"];
export const stylesheets = [];
export const fonts = [];
