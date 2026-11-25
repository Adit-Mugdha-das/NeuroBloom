<script>
	import { locale, localeText } from '$lib/i18n';

	const notice = {
		en: 'Research prototype for demonstrations with synthetic data. Do not enter real patient information.',
		bn: 'এটি সিন্থেটিক ডেটা দিয়ে প্রদর্শনের জন্য একটি গবেষণা প্রোটোটাইপ। প্রকৃত রোগীর তথ্য প্রবেশ করাবেন না।'
	};
</script>

<p class="demo-data-notice" role="note">{localeText(notice, $locale)}</p>

<style>
	.demo-data-notice {
		margin: 0 0 1rem;
		padding: 0.6rem 0.8rem;
		border: 1px solid #f59e0b;
		border-radius: 0.5rem;
		background: #fffbeb;
		color: #92400e;
		font-size: 0.82rem;
		line-height: 1.4;
	}
</style>
