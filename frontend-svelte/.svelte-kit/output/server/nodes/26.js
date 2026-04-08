

export const index = 26;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/doctor/notifications/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/26.C-YanTZV.js"];
export const stylesheets = [];
export const fonts = [];
