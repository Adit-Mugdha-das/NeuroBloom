

export const index = 28;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/patient/_id_/prescriptions/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/28.CEVdWdYN.js"];
export const stylesheets = [];
export const fonts = [];
