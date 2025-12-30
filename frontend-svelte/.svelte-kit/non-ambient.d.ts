
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
		RouteId(): "/" | "/baseline" | "/baseline/results" | "/baseline/tasks" | "/baseline/tasks/attention" | "/baseline/tasks/flexibility" | "/baseline/tasks/planning" | "/baseline/tasks/processing-speed" | "/baseline/tasks/visual-scanning" | "/baseline/tasks/working-memory" | "/dashboard" | "/empty-states-preview" | "/login" | "/progress" | "/register" | "/session-summary" | "/training" | "/training/digit-span" | "/training/inspection-time" | "/training/letter-number-sequencing" | "/training/operation-span" | "/training/pasat" | "/training/pattern-comparison" | "/training/sdmt" | "/training/spatial-span" | "/training/stroop" | "/training/trail-making-a";
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
			"/empty-states-preview": Record<string, never>;
			"/login": Record<string, never>;
			"/progress": Record<string, never>;
			"/register": Record<string, never>;
			"/session-summary": Record<string, never>;
			"/training": Record<string, never>;
			"/training/digit-span": Record<string, never>;
			"/training/inspection-time": Record<string, never>;
			"/training/letter-number-sequencing": Record<string, never>;
			"/training/operation-span": Record<string, never>;
			"/training/pasat": Record<string, never>;
			"/training/pattern-comparison": Record<string, never>;
			"/training/sdmt": Record<string, never>;
			"/training/spatial-span": Record<string, never>;
			"/training/stroop": Record<string, never>;
			"/training/trail-making-a": Record<string, never>
		};
		Pathname(): "/" | "/baseline" | "/baseline/" | "/baseline/results" | "/baseline/results/" | "/baseline/tasks" | "/baseline/tasks/" | "/baseline/tasks/attention" | "/baseline/tasks/attention/" | "/baseline/tasks/flexibility" | "/baseline/tasks/flexibility/" | "/baseline/tasks/planning" | "/baseline/tasks/planning/" | "/baseline/tasks/processing-speed" | "/baseline/tasks/processing-speed/" | "/baseline/tasks/visual-scanning" | "/baseline/tasks/visual-scanning/" | "/baseline/tasks/working-memory" | "/baseline/tasks/working-memory/" | "/dashboard" | "/dashboard/" | "/empty-states-preview" | "/empty-states-preview/" | "/login" | "/login/" | "/progress" | "/progress/" | "/register" | "/register/" | "/session-summary" | "/session-summary/" | "/training" | "/training/" | "/training/digit-span" | "/training/digit-span/" | "/training/inspection-time" | "/training/inspection-time/" | "/training/letter-number-sequencing" | "/training/letter-number-sequencing/" | "/training/operation-span" | "/training/operation-span/" | "/training/pasat" | "/training/pasat/" | "/training/pattern-comparison" | "/training/pattern-comparison/" | "/training/sdmt" | "/training/sdmt/" | "/training/spatial-span" | "/training/spatial-span/" | "/training/stroop" | "/training/stroop/" | "/training/trail-making-a" | "/training/trail-making-a/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/favicon.png" | string & {};
	}
}