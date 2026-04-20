export const BASELINE_MODULES = Object.freeze([
	{
		key: 'working_memory',
		title: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমরি' },
		route: '/baseline/tasks/working-memory',
		description: {
			en: 'Measure how well you can hold and use information in mind.',
			bn: 'মনে তথ্য ধরে রাখা ও ব্যবহার করার দক্ষতা মাপুন।'
		}
	},
	{
		key: 'attention',
		title: { en: 'Attention', bn: 'মনোযোগ' },
		route: '/baseline/tasks/attention',
		description: {
			en: 'Measure focus, inhibition, and sustained concentration.',
			bn: 'ফোকাস, ইনহিবিশন এবং দীর্ঘস্থায়ী মনোযোগ মাপুন।'
		}
	},
	{
		key: 'flexibility',
		title: { en: 'Cognitive Flexibility', bn: 'কগনিটিভ ফ্লেক্সিবিলিটি' },
		route: '/baseline/tasks/flexibility',
		description: {
			en: 'Measure how smoothly you can shift rules and mental sets.',
			bn: 'নিয়ম ও মানসিক সেট কত সহজে বদলাতে পারেন তা মাপুন।'
		}
	},
	{
		key: 'planning',
		title: { en: 'Planning', bn: 'পরিকল্পনা' },
		route: '/baseline/tasks/planning',
		description: {
			en: 'Measure structured problem solving and forward planning.',
			bn: 'গঠিত সমস্যা সমাধান ও অগ্রিম পরিকল্পনার দক্ষতা মাপুন।'
		}
	},
	{
		key: 'processing_speed',
		title: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
		route: '/baseline/tasks/processing-speed',
		description: {
			en: 'Measure how quickly you can take in and respond to information.',
			bn: 'তথ্য কত দ্রুত গ্রহণ ও তার জবাব দিতে পারেন তা মাপুন।'
		}
	},
	{
		key: 'visual_scanning',
		title: { en: 'Visual Scanning', bn: 'ভিজ্যুয়াল স্ক্যানিং' },
		route: '/baseline/tasks/visual-scanning',
		description: {
			en: 'Measure how efficiently you can search and track visual targets.',
			bn: 'দৃশ্যমান লক্ষ্য কত দক্ষভাবে খুঁজে ও ট্র্যাক করতে পারেন তা মাপুন।'
		}
	}
]);

export function getNextBaselineModule(taskStatus = {}) {
	return BASELINE_MODULES.find((module) => !taskStatus?.[module.key]) || null;
}
