# TOASTED — Plan Grading Rubric

## How to use this document
When the developer generates a test plan, they feed it to the grading AI along with the user profile and this rubric. The AI grades each criterion and gives an overall score. Plans must score 8/10 minimum across all test cases.

---

## GRADING INSTRUCTIONS FOR THE AI

You are grading a training plan generated for a specific user. You have been given:
1. The user's profile (goal, days, experience, equipment, injuries, severity, phase)
2. The generated plan (exercises, sets, reps, RPE, session structure, day labels)
3. This grading rubric

Score each criterion below. Then calculate the total. Be strict — an 8/10 plan should be genuinely good. A 10/10 plan should be what a top-tier physio and S&C coach would write together.

---

## CRITERION 1: SAFETY (0-15 points) — MOST IMPORTANT

### 1A: Banned movement compliance (0-5)
- 5 = Zero exercises violate the condition's restrictions for the current phase
- 3 = One exercise is borderline (could be argued either way)
- 0 = Any exercise clearly violates a known restriction for this condition/phase

Check specifically:
- ACL post-op Phase 1-2: no open chain knee extension past 45°, no running, no reactive plyometrics, no cutting
- MCL Phase 1: no deep knee flexion past ~70°, no valgus-loading exercises, no cutting/COD, no lateral plyometrics
- PCL: no heavy isolated hamstring loading in early phases (hamstrings stress PCL)
- Ankle Phase 1: no running, no jumping, no cutting, no high-impact
- Shoulder RC Phase 1: no overhead pressing at full load, no heavy overhead work
- Patellar tendinopathy: no excessive jump volume, respect pain monitoring
- LBP flexion-sensitive: no heavy deadlifts from floor, no loaded forward flexion
- LBP extension-sensitive: no prone extensions, limit overhead pressing

### 1B: Rehab block placement (0-3)
- 3 = Rehab warm-up at the START of every session that loads the affected region. Rehab accessories at the END of affected-region days. Home sessions on rest days (if applicable).
- 2 = Rehab blocks present but placement is suboptimal (e.g., accessories in the middle of the session)
- 1 = Rehab blocks present but missing from some affected-region days
- 0 = No rehab blocks, or rehab blocks only on non-affected days

### 1C: Regional proportionality (0-3)
- 3 = Unaffected regions are truly unaffected. A knee injury does NOT modify upper body days. A shoulder injury does NOT modify lower body days.
- 2 = Mostly proportional but some unnecessary modifications to unaffected regions
- 1 = Significant unnecessary modifications to unaffected regions
- 0 = The plan treats the entire body as injured when only one region is affected

### 1D: Red flag respect (0-2)
- 2 = If the profile includes red flag indicators, NO plan is generated and the user is directed to a medical professional
- 0 = Plan generated despite red flag indicators

### 1E: Clinician restriction respect (0-2)
- 2 = If the user reported clinician restrictions (e.g., "no running for 6 months"), the plan respects these absolutely
- 0 = Plan includes activities that violate stated clinician restrictions

---

## CRITERION 2: EXERCISE SELECTION (0-15 points)

**For Rehab Only mode: Score this criterion based on rehab exercise selection quality. 2A becomes "exercise appropriateness for the condition and phase" rather than "for goal." 2B becomes "exercise appropriateness for the user's functional level." 2E becomes "variety of rehab approaches across the week."**

### 2A: Exercise appropriateness for goal (0-5)
- 5 = Exercises genuinely serve the stated goal. Strength plans have compound lifts at appropriate intensities (RPE 7-9, 3-6 reps). Hypertrophy plans have moderate loads with higher volume (RPE 6-8, 8-15 reps). Speed plans have sprint work, plyometrics, and supportive strength. Conditioning plans have interval work and circuits.
- 3 = Mostly appropriate but some exercises don't clearly serve the goal
- 1 = Generic exercise selection that doesn't reflect the specific goal
- 0 = Exercises actively contradict the goal (e.g., endurance work in a strength plan, no sprinting in a speed plan)

### 2B: Exercise appropriateness for experience level (0-3)
- 3 = Beginners get simple movements (goblet squats, machine work, DB pressing). Intermediates get barbell compounds with moderate complexity. Advanced get complex movements, variations, and higher intensities.
- 2 = Mostly appropriate but one or two exercises are too advanced or too basic
- 1 = Significant mismatch between experience and exercise complexity
- 0 = Beginner given Olympic lifts or advanced given only machine work

### 2C: Exercise appropriateness for equipment (0-3)
- 3 = Every exercise can be performed with the user's stated equipment
- 2 = One exercise requires equipment the user doesn't have (but alternatives exist)
- 0 = Multiple exercises require unavailable equipment

### 2D: No duplicates within a day (0-2)
- 2 = No exercise appears twice on the same day
- 1 = One duplicate within a day
- 0 = Multiple duplicates within a day

### 2E: Exercise variety across the week (0-2)
- 2 = Good variety — different exercises on different days targeting the same muscle groups from different angles/patterns
- 1 = Some repetition across days (same exercise on day 1 and day 3)
- 0 = Copy-paste days with identical exercises

---

## CRITERION 3: PLAN STRUCTURE (0-15 points)

### 3A: Session time budget (0-3)
- 3 = Each session's estimated total time (all exercises × sets × reps × rest + warm-up + accessories) is within ±15% of the stated session length
- 2 = Within ±25%
- 1 = Within ±40%
- 0 = Session would clearly take twice as long or half as long as stated

Estimation guide:
- Compound exercise: sets × (reps × 3-4 seconds + rest period)
- Isolation exercise: sets × (reps × 2-3 seconds + rest period)
- Rehab warm-up block: 8-12 minutes
- Rehab accessory block: 10-15 minutes
- Speed work: include full recovery between reps

### 3B: Exercise count per session (0-3)
- 3 = Appropriate exercise count for the session length:
  - 30 min session: 3-5 exercises
  - 45 min session: 4-6 exercises
  - 60 min session: 5-8 exercises
  - 75 min session: 6-9 exercises
  - 90 min session: 7-11 exercises
  (These counts include rehab exercises for Both mode)
- 2 = Slightly over or under (±1-2 exercises)
- 1 = Significantly over or under
- 0 = Clearly wrong (3 exercises for a 90 min session, or 15 exercises for a 30 min session)

### 3C: Sets and reps appropriateness (0-3)
- 3 = Sets and reps match the goal:
  - Strength: 3-5 sets, 1-6 reps, RPE 7.5-9.5
  - Hypertrophy: 3-4 sets, 8-15 reps, RPE 6-8.5
  - Speed: 3-6 reps for sprints, full recovery, supporting strength at 3-5 sets × 3-6 reps
  - Conditioning: intervals with work:rest ratios, circuits with timed sets
  - Rehab: 2-4 sets, 10-20 reps typically, RPE 3-6 depending on phase
- 2 = Mostly appropriate, one or two exercises have odd prescriptions
- 1 = Multiple exercises have inappropriate prescriptions for the goal
- 0 = Prescriptions don't match the goal at all

### 3D: Day labelling honesty (0-3)
- 3 = Day labels accurately describe the content. If most speed exercises were removed due to injury, the day is NOT called "Speed Day" — it's honest about what it actually is.
- 2 = Labels are mostly accurate
- 1 = Labels are misleading (day called "Speed" but contains no speed work)
- 0 = Labels actively misrepresent the content

### 3E: Progressive structure across the week (0-3)
- 3 = The week has a logical structure: hard/easy day alternation, upper/lower or push/pull splits that make sense, rest days positioned appropriately, not all hard sessions back-to-back
- 2 = Mostly logical but one questionable placement
- 1 = Poor structure (e.g., two heavy squat days back-to-back)
- 0 = No apparent structure to the week

---

## CRITERION 4: REHAB QUALITY (0-20 points) — Both mode and Rehab Only

**IMPORTANT: For Rehab Only mode, this criterion is the MOST IMPORTANT criterion alongside Safety. The entire plan IS rehab — grade it as such. Every sub-criterion below applies with full weight.**

(If Gym Only with no injuries, auto-score 20/20)

### 4A: Rehab exercises target the right tissues (0-5)
- 5 = Rehab exercises directly address the injured structure. MCL gets valgus stability work, quad activation, controlled knee loading. ACL gets quad strengthening, hamstring support, balance. Shoulder gets rotator cuff strengthening, scapular control. Ankle gets proprioception, calf strengthening, balance board.
- 3 = Rehab exercises are generally appropriate but miss some key areas
- 1 = Rehab exercises are generic and don't specifically target the condition
- 0 = Rehab exercises are inappropriate for the condition (e.g., heavy squatting as "rehab" for ACL Phase 1)

### 4B: Rehab dosing is appropriate for the phase (0-3)
- 3 = Phase 1: isometrics, light loading, high reps, low RPE (3-5). Phase 2: progressive loading, moderate RPE (5-7). Phase 3: near-normal loading, approaching gym-level intensity. Rehab exercises progress appropriately across phases.
- 2 = Mostly appropriate but some exercises are too aggressive or too conservative for the phase
- 0 = Dosing is clearly wrong for the phase (e.g., heavy single-leg squats in ACL Phase 1)

### 4C: Rehab warm-up content (0-3)
- 3 = Warm-up includes: blood flow component (bike/walk), activation/isometric for the affected region, mobility if applicable. Warm-up is 8-12 minutes. Warm-up actually prepares the tissue for the gym work that follows.
- 2 = Warm-up is present and reasonable but missing one component
- 1 = Warm-up is too short, too generic, or doesn't target the affected region
- 0 = No warm-up, or warm-up is just "jog for 5 minutes" regardless of condition

### 4D: Balance and proprioception inclusion (0-2)
- 2 = For lower limb injuries: single-leg balance work is included on at least 2 days per week. For upper limb: shoulder stability/control exercises included.
- 1 = Present but insufficient (only 1 day, or only one exercise)
- 0 = No balance/proprioception work despite a joint injury

### 4E: Rehab to gym transition logic (0-2)
- 2 = The plan clearly shows how rehab and gym work complement each other. Rehab warm-up leads into gym work. Rehab accessories build on the gym work. There's a logical flow, not just bolted-on extras.
- 1 = Rehab and gym feel disconnected — two separate programs crammed into one session
- 0 = Rehab blocks feel completely random

### 4F: Rehab session structure (0-3) — Rehab Only mode only
(If Both mode or Gym Only, auto-score 3/3)
- 3 = Session follows proper rehab structure: warm-up/blood flow → mobility/ROM → activation/isometrics → progressive strengthening → proprioception/balance → cool-down. Each component is present and appropriate.
- 2 = Structure is present but missing one component or order is suboptimal
- 1 = Structure is disorganised — exercises seem randomly ordered
- 0 = No apparent session structure

### 4G: Rehab variety across sessions (0-2) — Rehab Only mode only
(If Both mode or Gym Only, auto-score 2/2)
- 2 = Sessions vary in emphasis (strength-focused day vs mobility/proprioception day). Not identical sessions every day.
- 1 = Some variation but mostly the same
- 0 = Identical sessions on every day

---

## CRITERION 5: HONESTY & COMMUNICATION (0-10 points)

### 5A: Honest about limitations (0-4)
- 4 = If the injury prevents meaningful training of the stated goal, the plan says so clearly. "Your ACL recovery currently prevents sprint training. This plan focuses on rehab + strength preservation. Speed work returns when you pass Phase 3 criteria." If the plan CAN serve the goal, it doesn't over-warn.
- 2 = Somewhat honest but either over-warns (mild injury treated as career-ending) or under-warns (serious injury glossed over)
- 0 = Plan pretends to deliver on the goal when it clearly can't, or makes the user feel like their mild injury is devastating

### 5B: Explains modifications (0-3)
- 3 = When an exercise is modified or substituted, the plan notes why. "Belt squat replaces back squat (deep flexion avoided for MCL Phase 1)." "Landmine press replaces OHP (overhead loading limited for shoulder)."
- 2 = Some modifications explained but not all
- 1 = No explanations for modifications
- 0 = Modifications made without any acknowledgment

### 5C: Appropriate warnings (0-3)
- 3 = Appropriate dose notes and cautions present. "Monitor pain during this exercise — if >3/10, reduce load." "Controlled tempo, 3-second eccentric." At 2 days/week: warns about slower recovery. For post-surgical: reminds to attend clinical appointments.
- 2 = Some appropriate warnings
- 1 = No warnings or excessively cautious (every exercise has a scary warning)
- 0 = Dangerous exercises with no warnings, or fear-mongering throughout

---

## CRITERION 6: FREQUENCY HANDLING (0-5 points)

### 6A: Appropriate for the selected day count (0-3)
- 3 = At 2 days: full-body sessions, no redundant days, warning about limited frequency. At 3 days: good split, covers all major patterns. At 4 days: upper/lower or similar logical split. At 5-6: appropriate volume distribution, recovery days, no overtraining.
- 2 = Mostly appropriate but one day feels redundant or underloaded
- 1 = Split doesn't make sense for the day count
- 0 = 4-day program crammed into 2 days, or 2-day content stretched to 6 with filler

### 6B: Rehab frequency appropriate (0-2)
- 2 = Rehab exercises appear frequently enough for the condition. Injured tissue benefits from 3-5x/week exposure. If user has only 2 gym days, the plan suggests home sessions. If user has 5+ days, rehab is well-distributed.
- 1 = Rehab frequency is suboptimal but present
- 0 = Rehab only appears once per week despite an active injury

---

## CRITERION 7: MULTI-INJURY HANDLING (0-5 points)

(If single injury or no injury, auto-score 5/5)

### 7A: All injuries addressed (0-3)
- 3 = Every reported injury has appropriate rehab content in the plan. No injury is ignored. Each injury's restrictions are respected simultaneously. The combined restrictions don't create contradictions.
- 2 = All injuries acknowledged but one gets significantly less attention
- 1 = One injury appears to be ignored
- 0 = Multiple injuries ignored

### 7B: Time budget managed (0-2)
- 2 = With multiple injuries, the session time is realistically managed. If three injuries each need 15 min of rehab in a 60 min session, the plan acknowledges this and either extends sessions, adds days, or honestly says gym training will be limited.
- 1 = Time budget is tight but technically possible
- 0 = Plan clearly doesn't fit in the stated session length with multiple injury rehab blocks

---

## SCORING SUMMARY

| Criterion | Max Points |
|-----------|-----------|
| 1. Safety | 15 |
| 2. Exercise Selection | 15 |
| 3. Plan Structure | 15 |
| 4. Rehab Quality | 20 |
| 5. Honesty & Communication | 10 |
| 6. Frequency Handling | 5 |
| 7. Multi-Injury Handling | 5 |
| **TOTAL** | **85** |

### Convert to 1-10 scale:
- 77-85 points = 10/10 (exceptional — physio and S&C coach would approve without changes)
- 68-76 points = 9/10 (excellent — minor suggestions only)
- 60-67 points = 8/10 (good — passes quality gate, minor issues)
- 51-59 points = 7/10 (adequate — some issues need fixing)
- 43-50 points = 6/10 (below standard — significant issues)
- Below 43 = fail — do not ship

### MINIMUM PASS: 8/10 (60+ points) across ALL test cases

### MANDATORY FAIL CONDITIONS (regardless of total score):
- ANY score of 0 on Criterion 1A (banned movement compliance) = automatic fail
- ANY score of 0 on Criterion 1D (red flag respect) = automatic fail
- ANY score of 0 on Criterion 1E (clinician restriction respect) = automatic fail
- Safety criterion total below 10/15 = automatic fail

---

## TEST CASE MATRIX

The developer should generate and grade plans for AT MINIMUM these combinations:

### Easy cases (should score 9-10):
1. Strength + no injury + 4 days + intermediate + full gym
2. Hypertrophy + no injury + 3 days + beginner + full gym
3. Speed + no injury + 4 days + intermediate + full gym
4. Conditioning + no injury + 3 days + beginner + basic gym

### Moderate cases (should score 8-9):
5. Strength + shoulder RC Phase 1 + 4 days + intermediate + full gym (Both)
6. Hypertrophy + MCL Grade 1 Phase 1 + 4 days + intermediate + full gym (Both)
7. Speed + ankle sprain Grade 2 Phase 1 + 4 days + intermediate + full gym (Both)
8. Conditioning + anterior knee pain + 3 days + beginner + basic gym (Both)
9. Rehab Only + MCL Grade 2 + 4 days + 45 min
10. Rehab Only + ankle sprain + 3 days + 30 min

### Hard cases (should score 8+):
11. Speed + ACL post-op Phase 2 + 4 days + intermediate + full gym (Both) — expect honest relabelling
12. Strength + MCL Grade 3 Phase 1 + 2 days + 60 min + intermediate (Both) — tight time budget
13. Hypertrophy + shoulder RC + ankle sprain (multi-injury) + 4 days + full gym (Both)
14. Speed + ACL post-op Phase 1 + 3 days + intermediate (Both) — expect "can't serve speed" message
15. Rehab Only + ACL post-op Phase 2 + 2 days + 30 min — frequency warning expected

### Edge cases (should score 8+ or produce appropriate warnings):
16. Any goal + 3 injuries + 2 days + 45 min (Both) — expect "recommend Rehab Only or more days" warning
17. Strength + no injury + 2 days + 30 min + beginner + minimal equipment — should still produce something useful
18. Speed + MCL Grade 2 Phase 1 + 6 days + 90 min + advanced + full gym — lots of capacity, still restricted
19. Rehab Only + undiagnosed knee pain (gradual, anterior, 3+ months) — should route to generic anterior knee protocol
20. Rehab Only + "tight hips" (stiffness, no pain) — should route to mobility protocol, not rehab
21. Any profile with red flags (numbness + spine) — must NOT generate a plan
22. Any profile with clinician restriction "no running 6 months" — must respect absolutely

### Rehab-focused cases (should score 8+):
23. Rehab Only + ACL post-op Phase 1 + 4 days + 45 min — pure rehab plan expected
24. Rehab Only + undiagnosed "tight hips, no pain" + 3 days + 30 min — mobility protocol expected, not injury rehab
25. Rehab Only + shoulder RC tendinopathy + 5 days + 30 min — high-frequency short sessions
26. Rehab Only + patellar tendinopathy (reactive/acute) + 3 days + 45 min — isometric-heavy loading programme
27. Rehab Only + mechanical LBP (3+ months chronic) + 4 days + 45 min — movement-based approach, no fear-avoidance
# TOASTED — Grading Rubric Supplement: Sophistication + Question Alignment

## Append this to the main Grading Rubric after the existing Criterion 7.

---

## CRITERION 8: PROGRAMMING SOPHISTICATION (0-20 points) — NEW

This criterion separates world-class plans from generic ones. A plan can score 8/10 overall without this, but cannot score 10/10.

### 8A: Exercise sequencing within sessions (0-4)
- 4 = Perfect neurological sequencing: speed/power first → compounds second → isolation third → conditioning last. Rehab warm-up at start. No conditioning before speed work. No isolation before compounds.
- 3 = Mostly correct with one minor sequencing issue
- 2 = Some exercises clearly in the wrong position (e.g., bicep curls before deadlifts)
- 0 = Random exercise order with no apparent logic

### 8B: Weekly fatigue management (0-4)
- 4 = Hard/moderate/easy day structure is logical. No two maximal sessions back-to-back. Speed days follow rest days or easy days. At least one true recovery/easy day in 4+ day plans. 
- 3 = Mostly good but one questionable day placement
- 2 = Two hard days back-to-back with no acknowledgment
- 0 = All days are equally hard, or speed work follows heavy squat day

### 8C: Push/pull and movement pattern balance (0-3)
- 3 = Across the week: push:pull ratio ≥ 1:1 (ideally 1:1.5). Both knee-dominant AND hip-dominant lower body work. Both horizontal AND vertical planes for upper body. No major imbalance.
- 2 = Mostly balanced with one minor gap (e.g., no vertical pulling)
- 1 = Noticeable imbalance (all pushing, no pulling, or all squats no hinges)
- 0 = Severe imbalance

### 8D: Periodisation model appropriateness (0-3)
- 3 = Beginner: linear progression with clear "add weight when you hit all reps" instruction. Intermediate: undulating or block model with varying stimuli across weeks. Advanced: conjugate or complex periodisation with shifting emphasis. The model MATCHES the experience level.
- 2 = Periodisation present but not optimally matched to experience
- 1 = Generic "do the same thing every week" regardless of experience
- 0 = No periodisation concept, no progression model

### 8E: Rest period specificity (0-2)
- 2 = Rest periods are specific to the exercise type and goal: 3-5 min for heavy strength, 60-90s for hypertrophy, full recovery for sprints. Not "rest 90 seconds" for everything.
- 1 = Rest periods present but same for all exercises
- 0 = No rest periods specified

### 8F: Tempo prescription where relevant (0-2)
- 2 = Tempo specified for hypertrophy exercises (controlled eccentric), rehab eccentrics, and isometric holds (duration + joint angle). Not needed for every exercise — just where it changes the stimulus.
- 1 = Some tempo notes but inconsistent
- 0 = No tempo information on any exercise

### 8G: Context-appropriate programming (0-2)
- 2 = Plan reflects the user's life context: desk workers get extra posterior chain and thoracic mobility. Athletes get sport-specific movement patterns. Beginners get simple exercise variations. Advanced get complex variations. The plan FEELS personalised.
- 1 = Some context awareness but mostly generic
- 0 = Same plan regardless of whether user is a desk worker or athlete

---

## CRITERION 9: QUESTION-ANSWER ALIGNMENT (0-10 points) — NEW

This checks that the plan DIRECTLY reflects the user's onboarding answers. Every answer should visibly influence the plan.

### 9A: Goal alignment (0-2)
Check: Does the plan's exercise selection, rep ranges, and session structure clearly serve Q1's answer?
- 2 = Unmistakably aligned. A strength plan looks like a strength plan. A speed plan has sprints. A conditioning plan has intervals. You could identify the goal from the plan without being told.
- 1 = Generally aligned but could fit multiple goals
- 0 = Plan doesn't reflect the stated goal

### 9B: Day count respected (0-1)
Check: Does the plan have exactly the number of days from Q4 (gym) or Q23 (rehab)?
- 1 = Correct day count
- 0 = Wrong number of days

### 9C: Session length respected (0-1)
Check: Can each session be completed within the time from Q5 or Q24?
- 1 = Yes, within ±15%
- 0 = No, sessions clearly exceed stated time

### 9D: Experience level reflected (0-2)
Check: Does exercise complexity match Q6?
- 2 = Beginner gets goblet squats, machines, DBs. Intermediate gets barbell compounds. Advanced gets complex variations, paused reps, tempo work.
- 1 = Mostly appropriate but one or two exercises mismatched
- 0 = Beginner given Olympic lifts, or advanced given only machine work

### 9E: Equipment respected (0-1)
Check: Can every exercise be done with Q7's equipment?
- 1 = Yes
- 0 = No — exercises require unavailable equipment

### 9F: Injury severity reflected (0-2)
Check: Does the plan's restriction level match Q12 (grade) + Q13 (timeline) + Q14 (pain) + Q15 (function)?
- 2 = Grade 1 at 4 weeks with low pain gets mild restrictions. Grade 3 at 1 week with high pain gets heavy restrictions. The restriction level is PROPORTIONAL to the severity answers.
- 1 = Generally proportional but could be more nuanced
- 0 = Same restrictions regardless of severity

### 9G: Priority slider reflected (0-1) — Both mode only
Check: Does the gym/rehab time split reflect Q9?
- 1 = 80% gym priority → minimal rehab, maximum gym. 80% rehab priority → extensive rehab, limited gym. 50/50 → balanced.
- 0 = Priority slider appears to have no effect on the plan

---

## UPDATED SCORING SUMMARY

| Criterion | Max Points |
|-----------|-----------|
| 1. Safety | 15 |
| 2. Exercise Selection | 15 |
| 3. Plan Structure | 15 |
| 4. Rehab Quality | 20 |
| 5. Honesty & Communication | 10 |
| 6. Frequency Handling | 5 |
| 7. Multi-Injury Handling | 5 |
| 8. Programming Sophistication | 20 |
| 9. Question-Answer Alignment | 10 |
| **TOTAL** | **115** |

### Updated 1-10 scale:
- 104-115 = 10/10
- 92-103 = 9/10
- 81-91 = 8/10
- 69-80 = 7/10
- 58-68 = 6/10
- Below 58 = fail

### MINIMUM PASS: 8/10 (81+ points)

### Additional mandatory fails:
- Programming Sophistication (Criterion 8) below 12/20 = automatic fail (plan is generic)
- Question-Answer Alignment (Criterion 9) below 6/10 = automatic fail (plan ignores user's answers)

---

## ADDITIONAL RESEARCH PAPERS (S&C Programming Depth)

Add these to the Research Papers document:

### Periodisation & Programming
103. Harries SK, Lubans DR, Callister R (2015) "Systematic Review and Meta-analysis of Linear and Undulating Periodized Resistance Training Programs on Muscular Strength" — Journal of Strength & Conditioning Research.
104. Painter KB et al. (2012) "Strength Gains: Block Versus Daily Undulating Periodization Weight Training Among Track and Field Athletes" — International Journal of Sports Physiology and Performance.
105. DeWeese BH et al. (2015) "The training process: Planning for strength–power training in track and field" — Journal of Sport and Health Science. Block periodisation for athletes.
106. Turner A (2011) "The Science and Practice of Periodization: A Brief Review" — Strength & Conditioning Journal.

### Force-Velocity & Power
107. Jimenez-Reyes P et al. (2017) "Effectiveness of an Individualized Training Based on Force-Velocity Profiling during Jumping" — Frontiers in Physiology.
108. Samozino P et al. (2016) "A simple method for measuring power, force, velocity properties, and mechanical effectiveness in sprint running" — Scandinavian Journal of Medicine & Science in Sports.

### Training Load & Recovery
109. Impellizzeri FM et al. (2019) "Internal and External Training Load: 15 Years On" — International Journal of Sports Physiology and Performance.
110. Halson SL (2014) "Monitoring Training Load to Understand Fatigue in Athletes" — Sports Medicine. Session RPE and fatigue monitoring.

### Hypertrophy Specific
111. Schoenfeld BJ et al. (2016) "Effects of Resistance Training Frequency on Measures of Muscle Hypertrophy: A Systematic Review and Meta-Analysis" — Sports Medicine. Frequency dose-response for muscle growth.
112. Schoenfeld BJ, Grgic J (2018) "Evidence-Based Guidelines for Resistance Training Volume to Maximize Muscle Hypertrophy" — Strength & Conditioning Journal. Volume landmarks for hypertrophy.

### Exercise Selection Science
113. Contreras B et al. (2016) "A comparison of gluteus maximus, biceps femoris, and vastus lateralis EMG amplitude in the parallel, full, and front squat variations" — Journal of Applied Biomechanics.
114. Krings BM et al. (2019) "Comparison of Muscle Activation Patterns During the Back Squat and Belt Squat" — Exercise Science & Physical Education Conference Proceedings.
