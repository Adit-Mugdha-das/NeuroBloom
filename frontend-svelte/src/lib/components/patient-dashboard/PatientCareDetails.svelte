<script>
	export let localeCode = 'en';
	export let notifications = [];
	export let latestPrescription = null;
	export let doctor = null;
	export let assignedDoctor = false;
	export let hasWarning = false;
	export let prescriptionPdfUrl = '';

	function lt(en, bn) {
		return localeCode === 'bn' ? bn : en;
	}

	function formatDate(dateValue) {
		if (!dateValue) {
			return lt('Not yet', 'এখনও নয়');
		}

		return new Date(dateValue).toLocaleDateString(localeCode === 'bn' ? 'bn-BD' : 'en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<div class="care-details">
	{#if hasWarning}
		<p class="warning-copy">
			{lt(
				'Some care details could not be loaded right now.',
				'এই মুহূর্তে কিছু কেয়ার বিস্তারিত লোড করা যায়নি।'
			)}
		</p>
	{/if}

	<section class="detail-panel">
		<h4>{lt('Recent notifications', 'সাম্প্রতিক নোটিফিকেশন')}</h4>
		{#if notifications.length > 0}
			<ul class="detail-list">
				{#each notifications as notification}
					<li>
						<strong>{notification.title}</strong>
						<span>{notification.message}</span>
					</li>
				{/each}
			</ul>
		{:else}
			<p class="muted-copy">{lt('No recent notifications right now.', 'এই মুহূর্তে কোনো সাম্প্রতিক নোটিফিকেশন নেই।')}</p>
		{/if}
	</section>

	<section class="detail-panel">
		<h4>{lt('Latest prescription', 'সর্বশেষ প্রেসক্রিপশন')}</h4>
		{#if latestPrescription}
			<p class="detail-title">{latestPrescription.title}</p>
			<p class="muted-copy">{latestPrescription.summary || latestPrescription.patient_instructions}</p>
			<p class="muted-copy">
				{localeCode === 'bn'
					? `${formatDate(latestPrescription.created_at)} তারিখে দেওয়া হয়েছে`
					: `Issued ${formatDate(latestPrescription.created_at)}`}
			</p>
			{#if prescriptionPdfUrl}
				<a class="inline-btn" href={prescriptionPdfUrl} target="_blank" rel="noopener">
					{lt('Open Prescription PDF', 'প্রেসক্রিপশনের PDF খুলুন')}
				</a>
			{/if}
		{:else}
			<p class="muted-copy">{lt('No active prescription is available yet.', 'এখনও কোনো সক্রিয় প্রেসক্রিপশন পাওয়া যায়নি।')}</p>
		{/if}
	</section>

	<section class="detail-panel">
		<h4>{lt('Your care team', 'আপনার কেয়ার টিম')}</h4>
		{#if assignedDoctor && doctor}
			<div class="doctor-grid">
				<div class="doctor-row">
					<span class="doctor-label">{lt('Doctor', 'ডাক্তার')}</span>
					<span>{doctor.full_name}</span>
				</div>
				<div class="doctor-row">
					<span class="doctor-label">{lt('Specialization', 'বিশেষজ্ঞতা')}</span>
					<span>{doctor.specialization}</span>
				</div>
				{#if doctor.institution}
					<div class="doctor-row">
						<span class="doctor-label">{lt('Institution', 'প্রতিষ্ঠান')}</span>
						<span>{doctor.institution}</span>
					</div>
				{/if}
				<div class="doctor-row">
					<span class="doctor-label">{lt('Email', 'ইমেইল')}</span>
					<span>{doctor.email}</span>
				</div>
				{#if doctor.assigned_at}
					<div class="doctor-row">
						<span class="doctor-label">{lt('Under care since', 'কেয়ারে আছেন')}</span>
						<span>{formatDate(doctor.assigned_at)}</span>
					</div>
				{/if}
			</div>
		{:else}
			<p class="muted-copy">
				{lt(
					'No doctor is currently assigned. You can still continue your training normally.',
					'এই মুহূর্তে কোনো ডাক্তার নির্ধারিত নেই। তবুও আপনি স্বাভাবিকভাবে ট্রেনিং চালিয়ে যেতে পারবেন।'
				)}
			</p>
			<a class="inline-link" href="/find-doctor">{lt('Browse available doctors', 'উপলব্ধ ডাক্তার দেখুন')}</a>
		{/if}
	</section>
</div>

<style>
	.care-details {
		display: grid;
		gap: 0.9rem;
	}

	.warning-copy {
		margin: 0;
		padding: 0.9rem 1rem;
		border-radius: 16px;
		background: rgba(255, 251, 235, 0.98);
		border: 1px solid rgba(245, 158, 11, 0.3);
		color: #92400e;
		font-size: 0.95rem;
	}

	.detail-panel {
		padding: 1rem;
		border-radius: 18px;
		background: #ffffff;
		border: 1px solid rgba(203, 213, 225, 0.75);
	}

	.detail-panel h4,
	.detail-title,
	.muted-copy {
		margin: 0;
	}

	.detail-panel h4 {
		font-size: 1.05rem;
		color: #0f172a;
		margin-bottom: 0.75rem;
	}

	.detail-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: 0.75rem;
	}

	.detail-list li {
		display: grid;
		gap: 0.2rem;
	}

	.detail-list strong,
	.doctor-row span:last-child {
		color: #0f172a;
	}

	.detail-list span,
	.muted-copy {
		font-size: 0.96rem;
		line-height: 1.6;
		color: #475569;
	}

	.detail-title {
		font-size: 1.08rem;
		font-weight: 800;
		color: #0f172a;
	}

	.inline-btn,
	.inline-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		margin-top: 0.8rem;
		min-height: 46px;
		padding: 0.8rem 1rem;
		border-radius: 999px;
		font-weight: 800;
		text-decoration: none;
	}

	.inline-btn {
		background: #1d4ed8;
		color: #fff;
	}

	.inline-link {
		background: #eff6ff;
		color: #1d4ed8;
	}

	.doctor-grid {
		display: grid;
		gap: 0.7rem;
	}

	.doctor-row {
		display: grid;
		grid-template-columns: minmax(120px, 180px) minmax(0, 1fr);
		gap: 0.75rem;
		padding-bottom: 0.65rem;
		border-bottom: 1px solid rgba(203, 213, 225, 0.65);
	}

	.doctor-label {
		font-weight: 700;
		color: #475569;
	}

	@media (max-width: 640px) {
		.doctor-row {
			grid-template-columns: 1fr;
		}

		.inline-btn,
		.inline-link {
			width: 100%;
		}
	}
</style>
