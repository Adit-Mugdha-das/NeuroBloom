

export const index = 36;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/messages/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/36.BXeSn4QB.js"];
export const stylesheets = [];
export const fonts = [];
