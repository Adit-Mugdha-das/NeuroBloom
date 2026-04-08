

export const index = 27;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/patient/_id_/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/27.B9LNA3LZ.js"];
export const stylesheets = [];
export const fonts = [];
