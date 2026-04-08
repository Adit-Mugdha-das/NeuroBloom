

export const index = 9;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/interventions/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/9.BwCfpHmy.js"];
export const stylesheets = [];
export const fonts = [];
