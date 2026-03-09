# NeuroBloom Synthetic Demo Dataset Plan

## Purpose

This document translates the teacher's demo suggestion into a project-specific seed plan for NeuroBloom.

The goal is not to add random fake rows. The goal is to create a small, clinically believable synthetic dataset that makes the full system look alive during a demo:

- patient dashboard
- doctor dashboard
- doctor analytics
- progress reports
- digital biomarkers
- prescriptions
- messages
- risk alerts
- notifications

This dataset must be clearly synthetic, but structured like a real working clinical system.

## Key Principle

Use synthetic demo data, not pretend real patient data.

Recommended labeling:

- Synthetic Demo Dataset
- Demo Clinical Dataset
- Training and Evaluation Data Only

## Teacher Suggestion Mapped To NeuroBloom

The teacher suggested:

- 10 doctors
- 10 patients
- 80 to 120 training sessions
- baseline assessments
- assignments
- messages
- prescriptions
- reports

That suggestion is correct, but NeuroBloom has more features than that. To match this project properly, the demo dataset should also cover:

- training plans
- session context records for biomarkers
- doctor interventions
- risk alerts
- platform notifications

## What Exists In The Current Project

The current backend models confirm the following entities already exist and should drive the seed plan:

- `User` for patients
- `Doctor`
- `PatientAssignment`
- `BaselineAssessment`
- `TrainingPlan`
- `TrainingSession`
- `SessionContext`
- `ProgressReport`
- `DoctorIntervention`
- `Message`
- `Notification`
- `RiskAlert`

There is already simple seed support for test sessions and some individual task seeds, but there is not yet one professional, end-to-end synthetic clinical dataset generator.

## Important Schema Reality Check

The teacher's example includes fields like:

- age
- gender
- ms_type
- diagnosis_date
- assigned_doctor

NeuroBloom does not currently store all of those as first-class patient columns.

Current patient model supports:

- `full_name`
- `email`
- `date_of_birth`
- `diagnosis`
- `consent_to_share`
- `is_active`

So for the synthetic dataset, the realistic mapping should be:

- age: derived from `date_of_birth`
- ms type: included inside `diagnosis` text unless schema is expanded later
- diagnosis date: not currently stored directly in patient model
- assigned doctor: represented through `PatientAssignment`

This means the demo data can still look realistic, but the seeded values must follow the actual schema instead of the teacher's simplified example literally.

## Proposed Dataset Scope

### Accounts

- 10 doctors
- 10 patients

### Clinical Relationships

- 10 active patient-doctor assignments
- 1 primary doctor per patient for demo clarity

### Assessments And Training

- 10 baseline assessments
- 10 active training plans
- 80 to 120 training sessions total
- 80 to 120 session context records linked to training sessions

### Doctor-Facing Clinical Content

- 10 to 20 progress reports
- 12 to 18 doctor interventions
- 10 to 15 digital prescriptions
- 20 to 30 secure messages

### Monitoring And System Activity

- 2 to 4 risk alerts
- 3 to 6 admin notifications

## What The Demo Dataset Should Feel Like

The dataset should not make every patient look identical or uniformly improving. That looks fake immediately.

Instead, the seeded patients should represent different realistic stories.

### Suggested Patient Profiles

1. Improving steadily
2. Improving slowly with fatigue-related fluctuations
3. Strong baseline but inconsistent adherence
4. Low processing speed with meaningful recovery
5. Good cognition overall but poor sleep correlation
6. Plateau after initial improvement
7. Attention variability with high reaction-time inconsistency
8. High fatigue and elevated risk score
9. Recently enrolled patient with limited history
10. Mild decline requiring doctor intervention

These profiles are important because they activate different parts of NeuroBloom:

- progress charts
- biomarker trends
- risk alerts
- doctor notes
- prescription history
- patient messaging

## Doctor Dataset Design

Each doctor record should include:

- full name
- professional email
- password hash via existing auth logic or secure seed utility
- realistic license number
- specialization
- institution
- `is_verified = true`
- `is_active = true`

### Recommended Specialization Mix

- Neurology
- Neuropsychology
- Rehabilitation Medicine
- Cognitive Neurology
- MS Clinical Care

### Recommended Institution Mix

Use multiple institutions so the dashboard and prescription PDFs feel realistic. Example categories:

- teaching hospital
- neuroscience institute
- rehabilitation center
- MS specialty clinic
- medical college hospital

## Patient Dataset Design

Each patient record should include:

- full name
- patient email
- hashed password
- date of birth
- diagnosis text
- `consent_to_share = true`
- `is_active = true`

### Diagnosis Text Examples

Because the current patient model stores diagnosis as text, use realistic diagnosis labels such as:

- Relapsing-Remitting Multiple Sclerosis
- Secondary Progressive Multiple Sclerosis
- Primary Progressive Multiple Sclerosis
- Clinically Isolated Syndrome under monitoring

### Demo-Friendly Patient Characteristics

The data should imply different ages and severity patterns through:

- date of birth
- diagnosis wording
- baseline scores
- training adherence
- fatigue-related context values

## Assignments

Each patient should be assigned to one doctor through `PatientAssignment`.

Each assignment should also include:

- diagnosis
- treatment goal
- assigned date
- active status

### Treatment Goal Examples

- Improve processing speed and sustained attention
- Support working memory consistency during fatigue
- Strengthen executive planning and daily-task organization
- Monitor cognitive stability over time
- Reduce variability in attention and response speed

## Baseline Assessments

Each patient should have one baseline assessment because that is required to make progress and training-plan views believable.

Seed all six domain scores:

- working memory
- attention
- flexibility
- planning
- processing speed
- visual scanning

Also seed:

- overall score
- assessment duration
- raw baseline metrics JSON

### Baseline Design Rule

Do not make all baselines low. Use a spread such as:

- some patients weak in processing speed only
- some weak in attention and working memory
- some relatively balanced
- some weak in flexibility and planning

That creates believable individualized training plans.

## Training Plans

Each patient should receive one active training plan linked to the baseline.

Seed realistic values for:

- primary focus domains
- secondary focus domains
- maintenance domains
- recommended tasks
- initial difficulty per domain
- current difficulty per domain
- total sessions completed
- streak values
- last session date

### Training Plan Realism Rule

The weakest baseline domains should become primary focus areas. The seed data should reflect that logic instead of random values.

## Training Sessions

This is the most important part of the demo dataset.

The seeded sessions should not just exist. They should tell a story.

### Recommended Volume

- 8 to 12 sessions per patient
- total 80 to 120 sessions

### Recommended Task Mix

Use the actual tasks already present in NeuroBloom where possible, including baseline and expanded training tasks. Example task families:

- working memory
- processing speed
- attention
- flexibility
- planning
- visual scanning

If certain tasks are implemented and others are not, the seed script should only use real task codes already supported by the backend.

### Session Fields To Seed

- domain
- task type
- task code
- score
- accuracy
- average reaction time
- consistency
- errors
- difficulty before
- difficulty after
- duration
- completion date
- adaptation reason
- raw data JSON

### Realism Rules For Sessions

- early sessions should usually be weaker than later sessions for improving patients
- some patients should plateau after early gains
- some patients should fluctuate based on fatigue or adherence
- high-performing patients should still have bad days
- risk patients should show persistent decline or instability

## Session Context And Biomarkers

NeuroBloom has a richer analytics architecture than the teacher's summary described, so the synthetic dataset must also seed `SessionContext` records.

Each seeded training session should ideally have a linked session context entry containing realistic values for:

- fatigue level
- sleep quality
- sleep hours
- medication taken today
- hours since medication
- readiness level
- pain level
- stress level
- distractions present
- location
- time of day
- occasional notes

### Why This Matters

Without session context, the biomarker and advanced analytics views will look much less convincing.

This data drives believable examples of:

- fatigue correlation
- sleep correlation
- medication timing effects
- readiness trends
- high-variability patients

## Progress Reports

Each patient should have at least one report, but ideally the dataset should include both weekly and monthly examples where possible.

Each report should include:

- report period
- domain trend summaries
- score changes vs baseline
- adherence summary
- fatigue or variability observations
- doctor commentary

### Doctor Commentary Should Sound Realistic

Examples:

- Processing speed has improved over the last month, but performance remains sensitive to high-fatigue days.
- Working memory remains variable. Continue short, frequent training sessions and review medication timing.
- Attention performance has stabilized. Maintain current training schedule and reassess in two weeks.

## Prescriptions And Doctor Interventions

NeuroBloom already supports digital prescriptions through doctor interventions, so the seed plan should include them.

### Prescriptions

Seed 1 to 2 prescriptions for selected patients with realistic structure such as:

- medication or intervention name
- dosage or frequency
- duration
- purpose
- issue date
- status
- version metadata if needed

### Other Interventions

Also seed a smaller number of:

- clinical notes
- training recommendations
- plan adjustments

This makes the doctor workspace look active and credible.

## Messages

Seed secure doctor-patient messages that reflect actual clinical follow-up.

Examples:

- doctor encouraging adherence
- patient reporting fatigue or scheduling difficulty
- follow-up after a progress report
- prescription acknowledgement

### Message Tone Rule

Keep the tone professional and concise. Avoid long fake conversations.

## Risk Alerts

NeuroBloom includes risk alerts, so the demo dataset should activate this feature for a small number of patients.

Recommended coverage:

- 2 to 4 open or recently reviewed alerts

Example alert reasons:

- sustained performance decline
- very high fatigue with worsening consistency
- prolonged inactivity or missed sessions
- concerning variability in attention metrics

This will make the doctor portal and monitoring story much stronger during a demo.

## Notifications

Seed a few platform notifications so the interface does not look empty.

Recommended examples:

- feature update
- training reminder campaign
- research participation announcement

## Demo Credentials Strategy

For presentation purposes, the seed plan should generate a clean list of demo credentials.

Recommended approach:

- one simple password pattern for demo doctors
- one simple password pattern for demo patients
- separate markdown or console output listing demo accounts

This is for demo convenience only and should be clearly separated from production expectations.

## What The Seed Script Should Do

Recommended script target:

- `backend/scripts/seed_demo_clinical_data.py`

Recommended script workflow:

1. ensure required lookup or task data exists
2. create doctors
3. create patients
4. create assignments and enable consent
5. create baseline assessments
6. create training plans from baseline logic
7. create dated training sessions across a believable timeline
8. create matching session-context rows for biomarker realism
9. create doctor interventions and prescriptions
10. create messages
11. create progress reports
12. create risk alerts for selected cases
13. create notifications
14. print a clear seed summary and demo credentials

## Timeline Design For Realism

The synthetic records should not all share the same date.

Recommended timeline:

- baseline assessments 6 to 10 weeks ago
- training sessions spread across recent weeks
- some recent sessions in the last 7 days
- progress reports generated after enough sessions exist
- prescriptions and messages placed logically after assignment and activity

That timeline makes charts, reports, and recent-activity panels look real.

## Quality Rules For The Seeded Dataset

The final synthetic dataset should satisfy these rules:

- every patient has a complete story, not isolated rows
- every doctor-facing screen has meaningful data
- every patient-facing screen has believable history
- not every patient improves in the same way
- at least a few cases trigger advanced features like prescriptions, reports, and risk alerts
- data values are plausible for a medical cognitive-training system

## What I Would Include In The First Version

For the first professional demo-ready seed script, I would include:

- 10 verified active doctors
- 10 active patients with consent enabled
- 10 active assignments
- 10 baseline assessments
- 10 active training plans
- about 100 training sessions total
- about 100 linked session-context entries
- 10 monthly reports and a few weekly reports
- 12 digital prescriptions or structured interventions
- 24 secure messages
- 3 risk alerts
- 4 admin notifications

## What I Would Not Do In The First Version

To keep the seed script maintainable, I would avoid these in version one:

- trying to simulate every possible task if the task is not fully implemented
- overly complex free-text data generation
- unsupported demographic fields not present in the schema
- pretending the data is real clinical data

## Recommended Output Of This Planning Stage

After approval, the next step would be to implement a single synthetic data seed script that:

- is repeatable
- is safe to rerun with cleanup options
- uses the existing project models
- creates a realistic cross-feature demo dataset for NeuroBloom

This document is the project-specific blueprint for that seed script.