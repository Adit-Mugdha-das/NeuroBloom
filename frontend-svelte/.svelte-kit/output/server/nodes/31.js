

export const index = 31;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/prescriptions/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/31.DlMdNFj4.js"];
export const stylesheets = [];
export const fonts = [];
