// Shared wording that keeps task screens consistent with the manuscript:
// NeuroBloom task implementations are inspired by published paradigms but
// have no established psychometric or clinical validity, norms, or battery
// equivalence.

export const RESEARCH_TASK_NOTE = {
	en: 'This NeuroBloom task is an original software implementation inspired by an established cognitive paradigm. Its stimuli, timing, scoring, difficulty progression, and language versions are specific to NeuroBloom. Its psychometric and clinical validity has not been established. The results describe performance in this software task and must not be interpreted as a clinical test result.',
	bn: 'এই NeuroBloom কাজটি একটি প্রতিষ্ঠিত কগনিটিভ প্যারাডাইম থেকে অনুপ্রাণিত একটি মৌলিক সফটওয়্যার বাস্তবায়ন। এর উদ্দীপক, সময়, স্কোরিং, কঠিনতার ধাপ ও ভাষা সংস্করণ NeuroBloom-এর নিজস্ব। এর সাইকোমেট্রিক ও ক্লিনিক্যাল বৈধতা এখনো প্রতিষ্ঠিত হয়নি। ফলাফল শুধু এই সফটওয়্যার কাজে পারফরম্যান্স বর্ণনা করে; এগুলোকে ক্লিনিক্যাল পরীক্ষার ফল হিসেবে ব্যাখ্যা করা যাবে না।'
};

export const RAW_RESULTS_NOTE = {
	en: 'These results describe your performance in this NeuroBloom task. Scores may change with practice, task difficulty, language, device, and testing conditions. Clinical reference ranges have not been established for this task version.',
	bn: 'এই ফলাফল এই NeuroBloom কাজে আপনার পারফরম্যান্স বর্ণনা করে। অনুশীলন, কাজের কঠিনতা, ভাষা, ডিভাইস ও পরীক্ষার পরিবেশের কারণে স্কোর বদলাতে পারে। এই কাজের সংস্করণের জন্য ক্লিনিক্যাল রেফারেন্স সীমা এখনো নির্ধারিত হয়নি।'
};

export const ABOUT_TASK_TITLE = { en: 'About this task', bn: 'এই কাজ সম্পর্কে' };
export const ABOUT_RESULTS_TITLE = { en: 'About these results', bn: 'এই ফলাফল সম্পর্কে' };
export const SCORE_BANDS_TITLE = {
	en: 'Software score bands (developer-selected)',
	bn: 'সফটওয়্যার স্কোর ব্যান্ড (ডেভেলপার-নির্ধারিত)'
};
export const RESEARCH_CONTEXT_LABEL = { en: 'Research context', bn: 'গবেষণার প্রেক্ষাপট' };
export const RESEARCH_CONTEXT_SHORT = {
	en: 'The original paradigm has been studied in MS research; this NeuroBloom version has not been validated.',
	bn: 'মূল প্যারাডাইমটি MS গবেষণায় ব্যবহৃত হয়েছে; এই NeuroBloom সংস্করণটি যাচাই করা হয়নি।'
};

export function paradigmInspirationNote(paradigm) {
	const name = typeof paradigm === 'string' ? { en: paradigm, bn: paradigm } : paradigm;
	return {
		en: `Paradigm inspiration: ${name.en}. This NeuroBloom implementation is not the standardized clinical instrument or an administration of the BICAMS, MACFIMS, or CANTAB battery.`,
		bn: `প্যারাডাইম অনুপ্রেরণা: ${name.bn}। এই NeuroBloom বাস্তবায়নটি প্রমিত ক্লিনিক্যাল পরীক্ষা নয়, এবং BICAMS, MACFIMS বা CANTAB ব্যাটারির কোনো প্রয়োগও নয়।`
	};
}
