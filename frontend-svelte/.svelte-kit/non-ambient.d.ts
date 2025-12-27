
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
		RouteId(): "/" | "/baseline" | "/baseline/results" | "/baseline/tasks" | "/baseline/tasks/attention" | "/baseline/tasks/flexibility" | "/baseline/tasks/planning" | "/baseline/tasks/processing-speed" | "/baseline/tasks/visual-scanning" | "/baseline/tasks/working-memory" | "/dashboard" | "/login" | "/progress" | "/register" | "/training";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/baseline": Record<string, never>;
			"/baseline/results": Record<string, never>;
			"/baseline/tasks": Record<string, never>;
			"/baseline/tasks/attention": Record<string, never>;
			"/baseline/tasks/flexibility": Record<string, never>;
			"/baseline/tasks/planning": Record<string, never>;
			"/baseline/tasks/processing-speed": Record<string, never>;
			"/baseline/tasks/visual-scanning": Record<string, never>;
			"/baseline/tasks/working-memory": Record<string, never>;
			"/dashboard": Record<string, never>;
			"/login": Record<string, never>;
			"/progress": Record<string, never>;
			"/register": Record<string, never>;
			"/training": Record<string, never>
		};
		Pathname(): "/" | "/baseline" | "/baseline/" | "/baseline/results" | "/baseline/results/" | "/baseline/tasks" | "/baseline/tasks/" | "/baseline/tasks/attention" | "/baseline/tasks/attention/" | "/baseline/tasks/flexibility" | "/baseline/tasks/flexibility/" | "/baseline/tasks/planning" | "/baseline/tasks/planning/" | "/baseline/tasks/processing-speed" | "/baseline/tasks/processing-speed/" | "/baseline/tasks/visual-scanning" | "/baseline/tasks/visual-scanning/" | "/baseline/tasks/working-memory" | "/baseline/tasks/working-memory/" | "/dashboard" | "/dashboard/" | "/login" | "/login/" | "/progress" | "/progress/" | "/register" | "/register/" | "/training" | "/training/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}