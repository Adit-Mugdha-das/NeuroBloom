
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/baseline" | "/baseline/tasks" | "/baseline/tasks/attention" | "/baseline/tasks/flexibility" | "/baseline/tasks/working-memory" | "/dashboard" | "/login" | "/register";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/baseline": Record<string, never>;
			"/baseline/tasks": Record<string, never>;
			"/baseline/tasks/attention": Record<string, never>;
			"/baseline/tasks/flexibility": Record<string, never>;
			"/baseline/tasks/working-memory": Record<string, never>;
			"/dashboard": Record<string, never>;
			"/login": Record<string, never>;
			"/register": Record<string, never>
		};
		Pathname(): "/" | "/baseline" | "/baseline/" | "/baseline/tasks" | "/baseline/tasks/" | "/baseline/tasks/attention" | "/baseline/tasks/attention/" | "/baseline/tasks/flexibility" | "/baseline/tasks/flexibility/" | "/baseline/tasks/working-memory" | "/baseline/tasks/working-memory/" | "/dashboard" | "/dashboard/" | "/login" | "/login/" | "/register" | "/register/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}