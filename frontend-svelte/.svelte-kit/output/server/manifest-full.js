export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["favicon.png"]),
	mimeTypes: {".png":"image/png"},
	_: {
		client: {start:"_app/immutable/entry/start.1b12FnFH.js",app:"_app/immutable/entry/app.feKYwhZM.js",imports:["_app/immutable/entry/start.1b12FnFH.js","_app/immutable/chunks/Ckn0ZsGu.js","_app/immutable/chunks/B_svR1Ec.js","_app/immutable/entry/app.feKYwhZM.js","_app/immutable/chunks/B_svR1Ec.js","_app/immutable/chunks/D0ceBE4O.js","_app/immutable/chunks/Ky5-2dZi.js","_app/immutable/chunks/OKpv22AX.js","_app/immutable/chunks/BWFMkk5A.js","_app/immutable/chunks/1fMQUamX.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js')),
			__memo(() => import('./nodes/4.js')),
			__memo(() => import('./nodes/5.js')),
			__memo(() => import('./nodes/6.js')),
			__memo(() => import('./nodes/7.js')),
			__memo(() => import('./nodes/8.js')),
			__memo(() => import('./nodes/9.js')),
			__memo(() => import('./nodes/10.js')),
			__memo(() => import('./nodes/11.js')),
			__memo(() => import('./nodes/12.js')),
			__memo(() => import('./nodes/13.js')),
			__memo(() => import('./nodes/14.js')),
			__memo(() => import('./nodes/15.js')),
			__memo(() => import('./nodes/16.js')),
			__memo(() => import('./nodes/17.js')),
			__memo(() => import('./nodes/18.js')),
			__memo(() => import('./nodes/19.js')),
			__memo(() => import('./nodes/20.js')),
			__memo(() => import('./nodes/21.js')),
			__memo(() => import('./nodes/22.js')),
			__memo(() => import('./nodes/23.js')),
			__memo(() => import('./nodes/24.js')),
			__memo(() => import('./nodes/25.js')),
			__memo(() => import('./nodes/26.js')),
			__memo(() => import('./nodes/27.js')),
			__memo(() => import('./nodes/28.js')),
			__memo(() => import('./nodes/29.js')),
			__memo(() => import('./nodes/30.js')),
			__memo(() => import('./nodes/31.js')),
			__memo(() => import('./nodes/32.js')),
			__memo(() => import('./nodes/33.js')),
			__memo(() => import('./nodes/34.js')),
			__memo(() => import('./nodes/35.js')),
			__memo(() => import('./nodes/36.js')),
			__memo(() => import('./nodes/37.js')),
			__memo(() => import('./nodes/38.js')),
			__memo(() => import('./nodes/39.js')),
			__memo(() => import('./nodes/40.js')),
			__memo(() => import('./nodes/41.js')),
			__memo(() => import('./nodes/42.js')),
			__memo(() => import('./nodes/43.js')),
			__memo(() => import('./nodes/44.js')),
			__memo(() => import('./nodes/45.js')),
			__memo(() => import('./nodes/46.js')),
			__memo(() => import('./nodes/47.js')),
			__memo(() => import('./nodes/48.js')),
			__memo(() => import('./nodes/49.js')),
			__memo(() => import('./nodes/50.js')),
			__memo(() => import('./nodes/51.js')),
			__memo(() => import('./nodes/52.js')),
			__memo(() => import('./nodes/53.js')),
			__memo(() => import('./nodes/54.js')),
			__memo(() => import('./nodes/55.js')),
			__memo(() => import('./nodes/56.js')),
			__memo(() => import('./nodes/57.js')),
			__memo(() => import('./nodes/58.js')),
			__memo(() => import('./nodes/59.js')),
			__memo(() => import('./nodes/60.js')),
			__memo(() => import('./nodes/61.js')),
			__memo(() => import('./nodes/62.js')),
			__memo(() => import('./nodes/63.js')),
			__memo(() => import('./nodes/64.js')),
			__memo(() => import('./nodes/65.js')),
			__memo(() => import('./nodes/66.js')),
			__memo(() => import('./nodes/67.js')),
			__memo(() => import('./nodes/68.js')),
			__memo(() => import('./nodes/69.js')),
			__memo(() => import('./nodes/70.js')),
			__memo(() => import('./nodes/71.js')),
			__memo(() => import('./nodes/72.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			},
			{
				id: "/admin/analytics",
				pattern: /^\/admin\/analytics\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 4 },
				endpoint: null
			},
			{
				id: "/admin/audit-logs",
				pattern: /^\/admin\/audit-logs\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 5 },
				endpoint: null
			},
			{
				id: "/admin/dashboard",
				pattern: /^\/admin\/dashboard\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 6 },
				endpoint: null
			},
			{
				id: "/admin/departments",
				pattern: /^\/admin\/departments\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 7 },
				endpoint: null
			},
			{
				id: "/admin/doctors",
				pattern: /^\/admin\/doctors\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 8 },
				endpoint: null
			},
			{
				id: "/admin/interventions",
				pattern: /^\/admin\/interventions\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 9 },
				endpoint: null
			},
			{
				id: "/admin/messages",
				pattern: /^\/admin\/messages\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 10 },
				endpoint: null
			},
			{
				id: "/admin/notifications",
				pattern: /^\/admin\/notifications\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 11 },
				endpoint: null
			},
			{
				id: "/admin/patients",
				pattern: /^\/admin\/patients\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 12 },
				endpoint: null
			},
			{
				id: "/admin/research-data",
				pattern: /^\/admin\/research-data\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 13 },
				endpoint: null
			},
			{
				id: "/admin/system-health",
				pattern: /^\/admin\/system-health\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 14 },
				endpoint: null
			},
			{
				id: "/baseline/results",
				pattern: /^\/baseline\/results\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 15 },
				endpoint: null
			},
			{
				id: "/baseline/tasks/attention",
				pattern: /^\/baseline\/tasks\/attention\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 16 },
				endpoint: null
			},
			{
				id: "/baseline/tasks/flexibility",
				pattern: /^\/baseline\/tasks\/flexibility\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 17 },
				endpoint: null
			},
			{
				id: "/baseline/tasks/planning",
				pattern: /^\/baseline\/tasks\/planning\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 18 },
				endpoint: null
			},
			{
				id: "/baseline/tasks/processing-speed",
				pattern: /^\/baseline\/tasks\/processing-speed\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 19 },
				endpoint: null
			},
			{
				id: "/baseline/tasks/visual-scanning",
				pattern: /^\/baseline\/tasks\/visual-scanning\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 20 },
				endpoint: null
			},
			{
				id: "/baseline/tasks/working-memory",
				pattern: /^\/baseline\/tasks\/working-memory\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 21 },
				endpoint: null
			},
			{
				id: "/dashboard",
				pattern: /^\/dashboard\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 22 },
				endpoint: null
			},
			{
				id: "/doctor/analytics",
				pattern: /^\/doctor\/analytics\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 23 },
				endpoint: null
			},
			{
				id: "/doctor/dashboard",
				pattern: /^\/doctor\/dashboard\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 24 },
				endpoint: null
			},
			{
				id: "/doctor/messages",
				pattern: /^\/doctor\/messages\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 25 },
				endpoint: null
			},
			{
				id: "/doctor/notifications",
				pattern: /^\/doctor\/notifications\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 26 },
				endpoint: null
			},
			{
				id: "/doctor/patients",
				pattern: /^\/doctor\/patients\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 30 },
				endpoint: null
			},
			{
				id: "/doctor/patient/[id]",
				pattern: /^\/doctor\/patient\/([^/]+?)\/?$/,
				params: [{"name":"id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 27 },
				endpoint: null
			},
			{
				id: "/doctor/patient/[id]/prescriptions",
				pattern: /^\/doctor\/patient\/([^/]+?)\/prescriptions\/?$/,
				params: [{"name":"id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 28 },
				endpoint: null
			},
			{
				id: "/doctor/patient/[id]/reports",
				pattern: /^\/doctor\/patient\/([^/]+?)\/reports\/?$/,
				params: [{"name":"id","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 29 },
				endpoint: null
			},
			{
				id: "/doctor/prescriptions",
				pattern: /^\/doctor\/prescriptions\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 31 },
				endpoint: null
			},
			{
				id: "/doctor/reports",
				pattern: /^\/doctor\/reports\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 32 },
				endpoint: null
			},
			{
				id: "/empty-states-preview",
				pattern: /^\/empty-states-preview\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 33 },
				endpoint: null
			},
			{
				id: "/find-doctor",
				pattern: /^\/find-doctor\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 34 },
				endpoint: null
			},
			{
				id: "/login",
				pattern: /^\/login\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 35 },
				endpoint: null
			},
			{
				id: "/messages",
				pattern: /^\/messages\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 36 },
				endpoint: null
			},
			{
				id: "/notifications",
				pattern: /^\/notifications\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 37 },
				endpoint: null
			},
			{
				id: "/prescriptions",
				pattern: /^\/prescriptions\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 38 },
				endpoint: null
			},
			{
				id: "/progress",
				pattern: /^\/progress\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 39 },
				endpoint: null
			},
			{
				id: "/progress/achievements",
				pattern: /^\/progress\/achievements\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 40 },
				endpoint: null
			},
			{
				id: "/progress/domains",
				pattern: /^\/progress\/domains\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 41 },
				endpoint: null
			},
			{
				id: "/progress/history",
				pattern: /^\/progress\/history\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 42 },
				endpoint: null
			},
			{
				id: "/register",
				pattern: /^\/register\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 43 },
				endpoint: null
			},
			{
				id: "/session-summary",
				pattern: /^\/session-summary\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 44 },
				endpoint: null
			},
			{
				id: "/settings",
				pattern: /^\/settings\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 45 },
				endpoint: null
			},
			{
				id: "/training",
				pattern: /^\/training\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 46 },
				endpoint: null
			},
			{
				id: "/training/cancellation-test",
				pattern: /^\/training\/cancellation-test\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 47 },
				endpoint: null
			},
			{
				id: "/training/category-fluency",
				pattern: /^\/training\/category-fluency\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 48 },
				endpoint: null
			},
			{
				id: "/training/dccs",
				pattern: /^\/training\/dccs\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 49 },
				endpoint: null
			},
			{
				id: "/training/digit-span",
				pattern: /^\/training\/digit-span\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 50 },
				endpoint: null
			},
			{
				id: "/training/dual-n-back",
				pattern: /^\/training\/dual-n-back\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 51 },
				endpoint: null
			},
			{
				id: "/training/flanker",
				pattern: /^\/training\/flanker\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 52 },
				endpoint: null
			},
			{
				id: "/training/gonogo",
				pattern: /^\/training\/gonogo\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 53 },
				endpoint: null
			},
			{
				id: "/training/inspection-time",
				pattern: /^\/training\/inspection-time\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 54 },
				endpoint: null
			},
			{
				id: "/training/letter-number-sequencing",
				pattern: /^\/training\/letter-number-sequencing\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 55 },
				endpoint: null
			},
			{
				id: "/training/multiple-object-tracking",
				pattern: /^\/training\/multiple-object-tracking\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 56 },
				endpoint: null
			},
			{
				id: "/training/operation-span",
				pattern: /^\/training\/operation-span\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 57 },
				endpoint: null
			},
			{
				id: "/training/pasat",
				pattern: /^\/training\/pasat\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 58 },
				endpoint: null
			},
			{
				id: "/training/pattern-comparison",
				pattern: /^\/training\/pattern-comparison\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 59 },
				endpoint: null
			},
			{
				id: "/training/plus-minus",
				pattern: /^\/training\/plus-minus\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 60 },
				endpoint: null
			},
			{
				id: "/training/sdmt",
				pattern: /^\/training\/sdmt\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 61 },
				endpoint: null
			},
			{
				id: "/training/spatial-span",
				pattern: /^\/training\/spatial-span\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 62 },
				endpoint: null
			},
			{
				id: "/training/stockings-of-cambridge",
				pattern: /^\/training\/stockings-of-cambridge\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 63 },
				endpoint: null
			},
			{
				id: "/training/stroop",
				pattern: /^\/training\/stroop\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 64 },
				endpoint: null
			},
			{
				id: "/training/tower-of-london",
				pattern: /^\/training\/tower-of-london\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 65 },
				endpoint: null
			},
			{
				id: "/training/trail-making-a",
				pattern: /^\/training\/trail-making-a\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 66 },
				endpoint: null
			},
			{
				id: "/training/trail-making-b",
				pattern: /^\/training\/trail-making-b\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 67 },
				endpoint: null
			},
			{
				id: "/training/twenty-questions",
				pattern: /^\/training\/twenty-questions\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 68 },
				endpoint: null
			},
			{
				id: "/training/useful-field-of-view",
				pattern: /^\/training\/useful-field-of-view\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 69 },
				endpoint: null
			},
			{
				id: "/training/verbal-fluency",
				pattern: /^\/training\/verbal-fluency\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 70 },
				endpoint: null
			},
			{
				id: "/training/visual-search",
				pattern: /^\/training\/visual-search\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 71 },
				endpoint: null
			},
			{
				id: "/training/wcst",
				pattern: /^\/training\/wcst\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 72 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
