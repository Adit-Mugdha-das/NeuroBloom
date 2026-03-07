
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
		RouteId(): "/" | "/admin" | "/admin/analytics" | "/admin/dashboard" | "/admin/departments" | "/admin/doctors" | "/admin/interventions" | "/admin/messages" | "/admin/patients" | "/baseline" | "/baseline/results" | "/baseline/tasks" | "/baseline/tasks/attention" | "/baseline/tasks/flexibility" | "/baseline/tasks/planning" | "/baseline/tasks/processing-speed" | "/baseline/tasks/visual-scanning" | "/baseline/tasks/working-memory" | "/dashboard" | "/doctor" | "/doctor/dashboard" | "/doctor/messages" | "/doctor/patient" | "/doctor/patient/[id]" | "/doctor/patient/[id]/reports" | "/empty-states-preview" | "/find-doctor" | "/login" | "/messages" | "/progress" | "/register" | "/session-summary" | "/settings" | "/training" | "/training/cancellation-test" | "/training/category-fluency" | "/training/dccs" | "/training/digit-span" | "/training/flanker" | "/training/gonogo" | "/training/inspection-time" | "/training/letter-number-sequencing" | "/training/multiple-object-tracking" | "/training/operation-span" | "/training/pasat" | "/training/pattern-comparison" | "/training/plus-minus" | "/training/sdmt" | "/training/spatial-span" | "/training/stockings-of-cambridge" | "/training/stroop" | "/training/tower-of-london" | "/training/trail-making-a" | "/training/trail-making-b" | "/training/twenty-questions" | "/training/useful-field-of-view" | "/training/verbal-fluency" | "/training/visual-search" | "/training/wcst";
		RouteParams(): {
			"/doctor/patient/[id]": { id: string };
			"/doctor/patient/[id]/reports": { id: string }
		};
		LayoutParams(): {
			"/": { id?: string };
			"/admin": Record<string, never>;
			"/admin/analytics": Record<string, never>;
			"/admin/dashboard": Record<string, never>;
			"/admin/departments": Record<string, never>;
			"/admin/doctors": Record<string, never>;
			"/admin/interventions": Record<string, never>;
			"/admin/messages": Record<string, never>;
			"/admin/patients": Record<string, never>;
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
			"/doctor": { id?: string };
			"/doctor/dashboard": Record<string, never>;
			"/doctor/messages": Record<string, never>;
			"/doctor/patient": { id?: string };
			"/doctor/patient/[id]": { id: string };
			"/doctor/patient/[id]/reports": { id: string };
			"/empty-states-preview": Record<string, never>;
			"/find-doctor": Record<string, never>;
			"/login": Record<string, never>;
			"/messages": Record<string, never>;
			"/progress": Record<string, never>;
			"/register": Record<string, never>;
			"/session-summary": Record<string, never>;
			"/settings": Record<string, never>;
			"/training": Record<string, never>;
			"/training/cancellation-test": Record<string, never>;
			"/training/category-fluency": Record<string, never>;
			"/training/dccs": Record<string, never>;
			"/training/digit-span": Record<string, never>;
			"/training/flanker": Record<string, never>;
			"/training/gonogo": Record<string, never>;
			"/training/inspection-time": Record<string, never>;
			"/training/letter-number-sequencing": Record<string, never>;
			"/training/multiple-object-tracking": Record<string, never>;
			"/training/operation-span": Record<string, never>;
			"/training/pasat": Record<string, never>;
			"/training/pattern-comparison": Record<string, never>;
			"/training/plus-minus": Record<string, never>;
			"/training/sdmt": Record<string, never>;
			"/training/spatial-span": Record<string, never>;
			"/training/stockings-of-cambridge": Record<string, never>;
			"/training/stroop": Record<string, never>;
			"/training/tower-of-london": Record<string, never>;
			"/training/trail-making-a": Record<string, never>;
			"/training/trail-making-b": Record<string, never>;
			"/training/twenty-questions": Record<string, never>;
			"/training/useful-field-of-view": Record<string, never>;
			"/training/verbal-fluency": Record<string, never>;
			"/training/visual-search": Record<string, never>;
			"/training/wcst": Record<string, never>
		};
		Pathname(): "/" | "/admin" | "/admin/" | "/admin/analytics" | "/admin/analytics/" | "/admin/dashboard" | "/admin/dashboard/" | "/admin/departments" | "/admin/departments/" | "/admin/doctors" | "/admin/doctors/" | "/admin/interventions" | "/admin/interventions/" | "/admin/messages" | "/admin/messages/" | "/admin/patients" | "/admin/patients/" | "/baseline" | "/baseline/" | "/baseline/results" | "/baseline/results/" | "/baseline/tasks" | "/baseline/tasks/" | "/baseline/tasks/attention" | "/baseline/tasks/attention/" | "/baseline/tasks/flexibility" | "/baseline/tasks/flexibility/" | "/baseline/tasks/planning" | "/baseline/tasks/planning/" | "/baseline/tasks/processing-speed" | "/baseline/tasks/processing-speed/" | "/baseline/tasks/visual-scanning" | "/baseline/tasks/visual-scanning/" | "/baseline/tasks/working-memory" | "/baseline/tasks/working-memory/" | "/dashboard" | "/dashboard/" | "/doctor" | "/doctor/" | "/doctor/dashboard" | "/doctor/dashboard/" | "/doctor/messages" | "/doctor/messages/" | "/doctor/patient" | "/doctor/patient/" | `/doctor/patient/${string}` & {} | `/doctor/patient/${string}/` & {} | `/doctor/patient/${string}/reports` & {} | `/doctor/patient/${string}/reports/` & {} | "/empty-states-preview" | "/empty-states-preview/" | "/find-doctor" | "/find-doctor/" | "/login" | "/login/" | "/messages" | "/messages/" | "/progress" | "/progress/" | "/register" | "/register/" | "/session-summary" | "/session-summary/" | "/settings" | "/settings/" | "/training" | "/training/" | "/training/cancellation-test" | "/training/cancellation-test/" | "/training/category-fluency" | "/training/category-fluency/" | "/training/dccs" | "/training/dccs/" | "/training/digit-span" | "/training/digit-span/" | "/training/flanker" | "/training/flanker/" | "/training/gonogo" | "/training/gonogo/" | "/training/inspection-time" | "/training/inspection-time/" | "/training/letter-number-sequencing" | "/training/letter-number-sequencing/" | "/training/multiple-object-tracking" | "/training/multiple-object-tracking/" | "/training/operation-span" | "/training/operation-span/" | "/training/pasat" | "/training/pasat/" | "/training/pattern-comparison" | "/training/pattern-comparison/" | "/training/plus-minus" | "/training/plus-minus/" | "/training/sdmt" | "/training/sdmt/" | "/training/spatial-span" | "/training/spatial-span/" | "/training/stockings-of-cambridge" | "/training/stockings-of-cambridge/" | "/training/stroop" | "/training/stroop/" | "/training/tower-of-london" | "/training/tower-of-london/" | "/training/trail-making-a" | "/training/trail-making-a/" | "/training/trail-making-b" | "/training/trail-making-b/" | "/training/twenty-questions" | "/training/twenty-questions/" | "/training/useful-field-of-view" | "/training/useful-field-of-view/" | "/training/verbal-fluency" | "/training/verbal-fluency/" | "/training/visual-search" | "/training/visual-search/" | "/training/wcst" | "/training/wcst/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/favicon.png" | string & {};
	}
}