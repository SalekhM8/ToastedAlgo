/* ===================================================================
   TOASTED — Onboarding State Machine
   Complete multi-flow onboarding with routing, validation, and red flag screening.
   =================================================================== */

const Onboarding = (() => {
  "use strict";

  // -----------------------------------------------------------------
  // Diagnosis database (grouped by region)
  // -----------------------------------------------------------------
  const DIAGNOSIS_DB = {
    Knee: [
      "ACL reconstruction (post-op)",
      "ACL sprain — conservative management",
      "MCL sprain",
      "LCL sprain",
      "PCL sprain",
      "Meniscus repair (post-op)",
      "Meniscus trim / partial meniscectomy",
      "Patellar tendinopathy",
      "Anterior knee pain / patellofemoral",
      "Other knee condition"
    ],
    Ankle: [
      "Lateral ankle sprain",
      "High ankle sprain (syndesmosis)",
      "Achilles tendinopathy",
      "Other ankle condition"
    ],
    Hip: [
      "Hip adductor strain",
      "Hip labral tear",
      "Hip impingement (FAI)",
      "Other hip condition"
    ],
    Shoulder: [
      "Rotator cuff tendinopathy",
      "Shoulder instability (subluxation/dislocation)",
      "Shoulder surgery (post-op)",
      "Other shoulder condition"
    ],
    Elbow: [
      "Lateral epicondylalgia (tennis elbow)",
      "Medial epicondylalgia (golfer's elbow)",
      "Other elbow condition"
    ],
    Spine: [
      "LBP — flexion-sensitive",
      "LBP — extension-sensitive",
      "LBP — general / non-specific",
      "Other spine condition"
    ]
  };

  // Body regions for undiagnosed flow
  const BODY_REGIONS = [
    { id: "knee", label: "Knee", icon: "\uD83E\uDDBF" },
    { id: "ankle", label: "Ankle / Foot", icon: "\uD83E\uDDB6" },
    { id: "hip", label: "Hip / Groin", icon: "\uD83E\uDD3E" },
    { id: "shoulder", label: "Shoulder", icon: "\uD83D\uDCAA" },
    { id: "elbow", label: "Elbow / Wrist", icon: "\u270B" },
    { id: "spine", label: "Back / Spine", icon: "\uD83E\uDDD1" }
  ];

  // -----------------------------------------------------------------
  // State
  // -----------------------------------------------------------------
  let state = {
    currentStep: null,
    answers: {},
    injuries: [],
    currentInjury: {},
    currentInjuryIndex: 0,
    redFlagTriggered: null,
    history: [],
    totalEstimatedSteps: 10,
    completedSteps: 0
  };

  let onComplete = null;
  let onRedFlag = null;
  let containerEl = null;

  // -----------------------------------------------------------------
  // Step Definitions
  // All steps in the flow. Each has: id, render function, condition function
  // -----------------------------------------------------------------

  function init(container, callbacks) {
    containerEl = container;
    onComplete = callbacks.onComplete;
    onRedFlag = callbacks.onRedFlag;
    state = {
      currentStep: "goal",
      answers: {},
      injuries: [],
      currentInjury: {},
      currentInjuryIndex: 0,
      redFlagTriggered: null,
      history: [],
      totalEstimatedSteps: 10,
      completedSteps: 0
    };
    render();
  }

  // -----------------------------------------------------------------
  // Navigation helpers
  // -----------------------------------------------------------------
  function goTo(stepId) {
    state.history.push(state.currentStep);
    state.currentStep = stepId;
    state.completedSteps++;
    recalcTotalSteps();
    render();
  }

  function goBack() {
    if (state.history.length > 0) {
      state.currentStep = state.history.pop();
      state.completedSteps = Math.max(0, state.completedSteps - 1);
      render();
    }
  }

  function recalcTotalSteps() {
    const mode = state.answers.mode;
    const hasInjury = state.answers.has_injury === "yes";
    let est = 3; // goal + injury? + mode choice
    if (mode === "gym_only" || mode === "both") est += 4; // gym flow
    if (mode === "both") est += 3; // both extras
    if (hasInjury) est += 7 * (state.injuries.length || 1); // per injury
    if (mode === "rehab_only") est += 5; // rehab specifics
    if (hasInjury) est += 3; // red flags
    state.totalEstimatedSteps = Math.max(est, state.completedSteps + 1);
  }

  function getProgress() {
    return Math.min(
      (state.completedSteps / state.totalEstimatedSteps) * 100,
      98
    );
  }

  // -----------------------------------------------------------------
  // Render entry point
  // -----------------------------------------------------------------
  function render() {
    const stepRenderers = {
      goal: renderGoal,
      rehab_goal: renderRehabGoal,
      gym_goal: renderGymGoal,
      gym_goal_with_injury_check: renderGymGoalWithInjuryCheck,
      has_injury: renderHasInjury,
      injury_mode: renderInjuryMode,
      gym_days: renderGymDays,
      session_length: renderSessionLength,
      experience: renderExperience,
      equipment: renderEquipment,
      both_dedicated_rehab: renderBothDedicatedRehab,
      both_gym_sessions: renderBothGymSessions,
      both_rehab_sessions: renderBothRehabSessions,
      both_balance_slider: renderBothBalanceSlider,
      injury_diagnosed: renderInjuryDiagnosed,
      injury_diagnosis_select: renderDiagnosisSelect,
      injury_severity: renderInjurySeverity,
      injury_timeline: renderInjuryTimeline,
      injury_pain: renderInjuryPain,
      injury_functional: renderInjuryFunctional,
      injury_clinician: renderInjuryClinician,
      injury_clinician_text: renderInjuryClinicianText,
      undiag_region: renderUndiagRegion,
      undiag_description: renderUndiagDescription,
      undiag_when: renderUndiagWhen,
      undiag_duration: renderUndiagDuration,
      undiag_pain: renderUndiagPain,
      undiag_impact: renderUndiagImpact,
      another_injury: renderAnotherInjury,
      rehab_days: renderRehabDays,
      rehab_session_length: renderRehabSessionLength,
      rehab_equipment: renderRehabEquipment,
      rehab_seeing_physio: renderRehabSeeingPhysio,
      rehab_previous: renderRehabPrevious,
      redflag_neuro: renderRedFlagNeuro,
      redflag_symptoms: renderRedFlagSymptoms,
      redflag_medical: renderRedFlagMedical,
      redflag_block: renderRedFlagBlock
    };

    const renderer = stepRenderers[state.currentStep];
    if (renderer) {
      containerEl.innerHTML = "";
      // Progress bar
      const progressHTML = `
        <div class="progress-bar-container">
          <div class="progress-bar" style="width: ${getProgress()}%"></div>
        </div>
        <div class="progress-info">Step ${state.completedSteps + 1}</div>
      `;
      containerEl.insertAdjacentHTML("beforeend", progressHTML);

      const wrapper = document.createElement("div");
      wrapper.className = "onboarding-wrapper";
      containerEl.appendChild(wrapper);

      // Header
      const header = document.createElement("div");
      header.className = "app-header";
      header.innerHTML = `
        <div class="logo"><span>Toasted</span></div>
        <div class="tagline">Training Plan Generator</div>
      `;
      wrapper.appendChild(header);

      // Question card
      const card = document.createElement("div");
      card.className = "question-card";
      renderer(card);
      wrapper.appendChild(card);

      // Back button (if history exists)
      if (state.history.length > 0 && state.currentStep !== "redflag_block") {
        const backRow = document.createElement("div");
        backRow.className = "action-row center";
        backRow.style.marginTop = "12px";
        const backBtn = document.createElement("button");
        backBtn.className = "btn btn-ghost btn-sm";
        backBtn.textContent = "\u2190 Back";
        backBtn.addEventListener("click", goBack);
        backRow.appendChild(backBtn);
        wrapper.appendChild(backRow);
      }
    }
  }

  // -----------------------------------------------------------------
  // Helper: build a question card interior
  // -----------------------------------------------------------------
  function buildQuestion(card, { label, title, subtitle }) {
    if (label) {
      const l = document.createElement("div");
      l.className = "question-label";
      l.textContent = label;
      card.appendChild(l);
    }
    const t = document.createElement("h2");
    t.className = "question-title";
    t.textContent = title;
    card.appendChild(t);
    if (subtitle) {
      const s = document.createElement("p");
      s.className = "question-subtitle";
      s.textContent = subtitle;
      card.appendChild(s);
    }
  }

  function buildOptions(card, options, onClick, { gridClass, multiSelect, selected } = {}) {
    const grid = document.createElement("div");
    grid.className = "options-grid" + (gridClass ? " " + gridClass : "");

    options.forEach((opt) => {
      const btn = document.createElement("button");
      btn.className = "option-btn" + (multiSelect ? " multi-select" : "");

      // Check if selected
      if (selected) {
        if (Array.isArray(selected) && selected.includes(opt.value)) {
          btn.classList.add("selected");
        } else if (selected === opt.value) {
          btn.classList.add("selected");
        }
      }

      let inner = "";
      if (opt.icon) {
        inner += `<span class="option-icon">${opt.icon}</span>`;
      }
      inner += `<span class="option-text">`;
      inner += `<span class="option-title">${opt.label}</span>`;
      if (opt.desc) {
        inner += `<span class="option-desc">${opt.desc}</span>`;
      }
      inner += `</span>`;
      btn.innerHTML = inner;

      btn.addEventListener("click", () => onClick(opt.value, btn, grid));
      grid.appendChild(btn);
    });

    card.appendChild(grid);
    return grid;
  }

  function buildSlider(card, { min, max, step, initial, label, leftLabel, rightLabel, onChange }) {
    const container = document.createElement("div");
    container.className = "slider-container";

    const valueDisp = document.createElement("div");
    valueDisp.className = "slider-value";
    valueDisp.textContent = label ? label(initial) : initial;
    container.appendChild(valueDisp);

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = min;
    slider.max = max;
    slider.step = step || 1;
    slider.value = initial;

    // Set initial fill
    const pct = ((initial - min) / (max - min)) * 100;
    slider.style.setProperty("--fill", pct + "%");

    slider.addEventListener("input", () => {
      const val = parseFloat(slider.value);
      const p = ((val - min) / (max - min)) * 100;
      slider.style.setProperty("--fill", p + "%");
      valueDisp.textContent = label ? label(val) : val;
      if (onChange) onChange(val);
    });

    container.appendChild(slider);

    if (leftLabel || rightLabel) {
      const row = document.createElement("div");
      row.className = "slider-label-row";
      row.innerHTML = `<span>${leftLabel || ""}</span><span>${rightLabel || ""}</span>`;
      container.appendChild(row);
    }

    card.appendChild(container);
    return slider;
  }

  function buildContinueButton(card, text, onClick) {
    const row = document.createElement("div");
    row.className = "action-row end";
    const btn = document.createElement("button");
    btn.className = "btn btn-primary";
    btn.textContent = text || "Continue";
    btn.addEventListener("click", onClick);
    row.appendChild(btn);
    card.appendChild(row);
    return btn;
  }

  // ===================================================================
  // FLOW 1: PRIMARY PATH + MODE SELECTION
  // ===================================================================

  function renderGoal(card) {
    buildQuestion(card, {
      label: "Let's start",
      title: "What brings you here?",
      subtitle: "This determines your entire programme."
    });

    buildOptions(card, [
      {
        value: "gym",
        label: "I want to train",
        icon: "\uD83C\uDFCB\uFE0F",
        desc: "Gym programme — strength, hypertrophy, speed, conditioning"
      },
      {
        value: "rehab",
        label: "I need rehab",
        icon: "\uD83E\uDE79",
        desc: "Dedicated recovery programme for an injury or pain"
      },
      {
        value: "both",
        label: "Both — train + rehab",
        icon: "\uD83D\uDD04",
        desc: "Gym training with rehab integrated around your injury"
      }
    ], (value) => {
      if (value === "rehab") {
        state.answers.mode = "rehab_only";
        state.answers.has_injury = "yes";
        goTo("rehab_goal");
      } else if (value === "both") {
        state.answers.mode = "both";
        state.answers.has_injury = "yes";
        goTo("gym_goal");
      } else {
        goTo("gym_goal_with_injury_check");
      }
    });
  }

  function renderRehabGoal(card) {
    buildQuestion(card, {
      label: "Recovery goal",
      title: "What's your main recovery goal?",
      subtitle: "This shapes how we build your rehab programme."
    });

    buildOptions(card, [
      {
        value: "return_to_sport",
        label: "Get back to sport",
        icon: "\u26BD",
        desc: "Rehab focused on returning to athletic activity"
      },
      {
        value: "return_to_daily",
        label: "Get back to daily life",
        icon: "\uD83D\uDEB6",
        desc: "Stairs, lifting, walking — pain-free function"
      },
      {
        value: "pain_reduction",
        label: "Reduce my pain",
        icon: "\uD83D\uDE4F",
        desc: "Focus on pain management and gradual loading"
      },
      {
        value: "pre_surgery",
        label: "Prepare for surgery",
        icon: "\uD83C\uDFE5",
        desc: "Prehab — maximise strength before a planned procedure"
      },
      {
        value: "general_recovery",
        label: "General recovery",
        icon: "\uD83C\uDF31",
        desc: "Balanced rehab — strength, mobility, and function"
      }
    ], (value) => {
      state.answers.goal = value;
      goTo("injury_diagnosed");
    });
  }

  function renderGymGoalWithInjuryCheck(card) {
    buildQuestion(card, {
      label: "Training goal",
      title: "What's your primary training goal?",
      subtitle: "This shapes your entire programme."
    });

    buildOptions(card, [
      { value: "strength", label: "Strength", icon: "\uD83C\uDFCB\uFE0F", desc: "Get stronger — low rep, high load" },
      { value: "hypertrophy", label: "Hypertrophy", icon: "\uD83D\uDCAA", desc: "Build muscle mass" },
      { value: "speed", label: "Speed", icon: "\u26A1", desc: "Get faster — sprint & agility" },
      { value: "power", label: "Power", icon: "\uD83D\uDCA5", desc: "Explosive force — Olympic lifts, plyometrics" },
      { value: "conditioning", label: "Conditioning", icon: "\u2764\uFE0F", desc: "Improve work capacity & endurance" },
      { value: "general_fitness", label: "General Fitness", icon: "\uD83C\uDF1F", desc: "Balanced health & function" },
      { value: "athleticism", label: "Athleticism", icon: "\uD83C\uDFC6", desc: "All-round athletic performance" }
    ], (value) => {
      state.answers.goal = value;
      goTo("has_injury");
    });
  }

  function renderGymGoal(card) {
    buildQuestion(card, {
      label: "Training goal",
      title: "What's your primary training goal?",
      subtitle: "Your gym sessions will be built around this."
    });

    buildOptions(card, [
      { value: "strength", label: "Strength", icon: "\uD83C\uDFCB\uFE0F", desc: "Get stronger — low rep, high load" },
      { value: "hypertrophy", label: "Hypertrophy", icon: "\uD83D\uDCAA", desc: "Build muscle mass" },
      { value: "speed", label: "Speed", icon: "\u26A1", desc: "Get faster — sprint & agility" },
      { value: "power", label: "Power", icon: "\uD83D\uDCA5", desc: "Explosive force — Olympic lifts, plyometrics" },
      { value: "conditioning", label: "Conditioning", icon: "\u2764\uFE0F", desc: "Improve work capacity & endurance" },
      { value: "general_fitness", label: "General Fitness", icon: "\uD83C\uDF1F", desc: "Balanced health & function" },
      { value: "athleticism", label: "Athleticism", icon: "\uD83C\uDFC6", desc: "All-round athletic performance" }
    ], (value) => {
      state.answers.goal = value;
      goTo("gym_days");
    });
  }

  function renderHasInjury(card) {
    buildQuestion(card, {
      label: "Injury screening",
      title: "Do you currently have any injuries or pain?",
      subtitle: "We'll adapt your plan to keep you safe and progressing."
    });

    buildOptions(card, [
      { value: "yes", label: "Yes, I have an injury or pain", icon: "\uD83E\uDE79" },
      { value: "no", label: "No, I'm injury-free", icon: "\u2705" }
    ], (value) => {
      state.answers.has_injury = value;
      if (value === "no") {
        state.answers.mode = "gym_only";
        goTo("gym_days");
      } else {
        goTo("injury_mode");
      }
    });
  }

  function renderInjuryMode(card) {
    buildQuestion(card, {
      label: "Training mode",
      title: "How would you like to handle your injury?",
      subtitle: "Choose the approach that fits your situation."
    });

    buildOptions(card, [
      {
        value: "both",
        label: "Train around it",
        icon: "\uD83D\uDD04",
        desc: "Gym training with rehab integrated"
      },
      {
        value: "rehab_only",
        label: "Focus on recovery",
        icon: "\uD83E\uDE79",
        desc: "Dedicated rehab programme only"
      },
      {
        value: "gym_only_injured",
        label: "Train normally",
        icon: "\u26A0\uFE0F",
        desc: "Standard gym plan — injury acknowledged but not programmed"
      }
    ], (value) => {
      if (value === "gym_only_injured") {
        state.answers.mode = "gym_only";
        card.innerHTML = "";
        buildQuestion(card, {
          label: "Important note",
          title: "Training normally with an injury",
          subtitle: null
        });
        const alert = document.createElement("div");
        alert.className = "alert-block warning";
        alert.innerHTML = `
          <div class="alert-title">Proceed with caution</div>
          <div class="alert-body">
            You've chosen to train normally despite having an injury. Your plan will <strong>not include</strong> specific
            rehab exercises or modifications. If your pain increases, please stop and consult a physiotherapist.
            <br><br>
            We'll still ask about your injury for safety screening, but it won't affect exercise selection.
          </div>
        `;
        card.appendChild(alert);
        buildContinueButton(card, "I understand, continue", () => {
          goTo("gym_days");
        });
      } else {
        state.answers.mode = value;
        if (value === "both") {
          goTo("gym_days");
        } else {
          goTo("injury_diagnosed");
        }
      }
    });
  }

  // ===================================================================
  // FLOW 2: GYM PROFILE
  // ===================================================================

  function renderGymDays(card) {
    buildQuestion(card, {
      label: "Gym profile",
      title: "How many days per week can you train?",
      subtitle: "Be realistic — consistency beats volume."
    });

    buildOptions(card, [
      { value: 2, label: "2 days", desc: "Full body sessions" },
      { value: 3, label: "3 days", desc: "Full body or upper/lower" },
      { value: 4, label: "4 days", desc: "Upper/lower split" },
      { value: 5, label: "5 days", desc: "Push/pull/legs or similar" },
      { value: 6, label: "6 days", desc: "High frequency split" }
    ], (value) => {
      state.answers.days_per_week = value;
      goTo("session_length");
    }, { gridClass: "three-col" });
  }

  function renderSessionLength(card) {
    buildQuestion(card, {
      label: "Gym profile",
      title: "How long are your sessions?",
      subtitle: "Including warmup and cooldown."
    });

    buildOptions(card, [
      { value: 30, label: "30 min", icon: "\u23F1\uFE0F", desc: "Quick & efficient" },
      { value: 45, label: "45 min", icon: "\u23F1\uFE0F", desc: "Focused session" },
      { value: 60, label: "60 min", icon: "\u23F1\uFE0F", desc: "Standard session" },
      { value: 75, label: "75 min", icon: "\u23F1\uFE0F", desc: "Extended session" },
      { value: 90, label: "90 min", icon: "\u23F1\uFE0F", desc: "Full session" }
    ], (value) => {
      state.answers.session_minutes = value;
      goTo("experience");
    }, { gridClass: "three-col" });
  }

  function renderExperience(card) {
    buildQuestion(card, {
      label: "Gym profile",
      title: "What's your training experience?",
      subtitle: "Be honest — this affects exercise complexity and loading."
    });

    buildOptions(card, [
      {
        value: "beginner",
        label: "Beginner",
        icon: "\uD83C\uDF31",
        desc: "Less than 1 year consistent training"
      },
      {
        value: "intermediate",
        label: "Intermediate",
        icon: "\uD83C\uDF3F",
        desc: "1-3 years, comfortable with compound lifts"
      },
      {
        value: "advanced",
        label: "Advanced",
        icon: "\uD83C\uDF33",
        desc: "3+ years, experienced with periodisation"
      }
    ], (value) => {
      state.answers.experience = value;
      goTo("equipment");
    });
  }

  function renderEquipment(card) {
    buildQuestion(card, {
      label: "Gym profile",
      title: "What equipment do you have access to?",
      subtitle: "This determines exercise selection."
    });

    buildOptions(card, [
      {
        value: "full_gym",
        label: "Full gym",
        icon: "\uD83C\uDFCB\uFE0F",
        desc: "Barbells, dumbbells, cables, machines, racks"
      },
      {
        value: "basic_gym",
        label: "Basic gym",
        icon: "\uD83C\uDFE0",
        desc: "Dumbbells, bench, pull-up bar, some machines"
      },
      {
        value: "home_db_bands",
        label: "Home — DBs & bands",
        icon: "\uD83C\uDFE1",
        desc: "Dumbbells, resistance bands, maybe a bench"
      },
      {
        value: "minimal",
        label: "Minimal",
        icon: "\uD83E\uDDD8",
        desc: "Bodyweight, maybe a band or two"
      }
    ], (value) => {
      state.answers.equipment = value;
      if (state.answers.mode === "both") {
        goTo("both_dedicated_rehab");
      } else if (state.answers.has_injury === "yes" && state.answers.mode === "gym_only") {
        // Gym only but injured — still do injury assessment for screening
        goTo("injury_diagnosed");
      } else {
        // No injury, gym only — done
        finishOnboarding();
      }
    });
  }

  // ===================================================================
  // BOTH MODE EXTRAS
  // ===================================================================

  function renderBothDedicatedRehab(card) {
    buildQuestion(card, {
      label: "Rehab integration",
      title: "Would you like dedicated rehab sessions separate from gym days?",
      subtitle: "Or we can integrate rehab into your gym sessions."
    });

    buildOptions(card, [
      {
        value: "yes",
        label: "Yes — separate rehab sessions",
        icon: "\uD83D\uDCC5",
        desc: "Dedicated days for rehab exercises"
      },
      {
        value: "no",
        label: "No — integrate into gym sessions",
        icon: "\uD83D\uDD04",
        desc: "Rehab woven into warmup and accessories"
      }
    ], (value) => {
      state.answers.dedicated_rehab_days = value === "yes" ? "Yes" : "No";
      if (value === "yes") {
        goTo("both_gym_sessions");
      } else {
        goTo("both_balance_slider");
      }
    });
  }

  function renderBothGymSessions(card) {
    buildQuestion(card, {
      label: "Rehab integration",
      title: "How many gym sessions per week?",
      subtitle: `You said ${state.answers.days_per_week} total days. Split between gym and rehab.`
    });

    const maxGym = state.answers.days_per_week - 1;
    const options = [];
    for (let i = 1; i <= maxGym; i++) {
      options.push({
        value: i,
        label: `${i} gym session${i > 1 ? "s" : ""}`,
        desc: `${state.answers.days_per_week - i} rehab session${state.answers.days_per_week - i > 1 ? "s" : ""}`
      });
    }

    buildOptions(card, options, (value) => {
      state.answers.gym_sessions = value;
      state.answers.rehab_sessions = state.answers.days_per_week - value;
      goTo("both_balance_slider");
    });
  }

  function renderBothRehabSessions(card) {
    // This is only reached via alt routing; main route skips it
    buildQuestion(card, {
      label: "Rehab integration",
      title: "How many rehab sessions per week?",
      subtitle: "These are dedicated rehab-only sessions."
    });
    const options = [];
    for (let i = 1; i <= 5; i++) {
      options.push({ value: i, label: `${i} session${i > 1 ? "s" : ""}` });
    }
    buildOptions(card, options, (value) => {
      state.answers.rehab_sessions = value;
      goTo("both_balance_slider");
    }, { gridClass: "three-col" });
  }

  function renderBothBalanceSlider(card) {
    buildQuestion(card, {
      label: "Rehab integration",
      title: "What's the gym vs rehab priority balance?",
      subtitle: "Slide to set how much of your session time goes to gym vs rehab."
    });

    let currentValue = 50;
    const slider = buildSlider(card, {
      min: 20,
      max: 80,
      step: 10,
      initial: 50,
      label: (v) => `${v}% Gym / ${100 - v}% Rehab`,
      leftLabel: "More Rehab",
      rightLabel: "More Gym",
      onChange: (v) => { currentValue = v; }
    });

    buildContinueButton(card, "Continue", () => {
      state.answers.priority_slider = `${currentValue}/${100 - currentValue}`;
      goTo("injury_diagnosed");
    });
  }

  // ===================================================================
  // FLOW 3: INJURY ASSESSMENT
  // ===================================================================

  function renderInjuryDiagnosed(card) {
    const injNum = state.currentInjuryIndex + 1;
    state.currentInjury = {};

    buildQuestion(card, {
      label: `Injury ${injNum}`,
      title: "Do you have a diagnosis for this injury?",
      subtitle: "A formal diagnosis from a healthcare professional."
    });

    buildOptions(card, [
      { value: "yes", label: "Yes, I have a diagnosis", icon: "\uD83D\uDCCB" },
      { value: "no", label: "No, it's undiagnosed", icon: "\u2753" }
    ], (value) => {
      state.currentInjury.diagnosed = value === "yes";
      if (value === "yes") {
        goTo("injury_diagnosis_select");
      } else {
        goTo("undiag_region");
      }
    });
  }

  // -----------------------------------------------------------------
  // FLOW 3A: Diagnosed
  // -----------------------------------------------------------------

  function renderDiagnosisSelect(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Diagnosis`,
      title: "What is your diagnosis?",
      subtitle: "Search or browse by body region."
    });

    // Search input
    const searchWrap = document.createElement("div");
    searchWrap.className = "search-input-wrapper";
    searchWrap.innerHTML = `<span class="search-icon">\uD83D\uDD0D</span>`;
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.className = "text-input";
    searchInput.placeholder = "Search diagnoses...";
    searchWrap.appendChild(searchInput);
    card.appendChild(searchWrap);

    // Diagnosis list
    const listEl = document.createElement("div");
    listEl.className = "diagnosis-list";
    card.appendChild(listEl);

    function renderList(filter) {
      listEl.innerHTML = "";
      let hasResults = false;
      const filterLower = (filter || "").toLowerCase();

      for (const [region, diagnoses] of Object.entries(DIAGNOSIS_DB)) {
        const filtered = diagnoses.filter(
          (d) => !filterLower || d.toLowerCase().includes(filterLower)
        );
        if (filtered.length === 0) continue;
        hasResults = true;

        const header = document.createElement("div");
        header.className = "diagnosis-group-header";
        header.textContent = region;
        listEl.appendChild(header);

        filtered.forEach((diag) => {
          const item = document.createElement("div");
          item.className = "diagnosis-item";
          item.textContent = diag;
          item.addEventListener("click", () => {
            state.currentInjury.condition = diag;
            state.currentInjury.region = region.toLowerCase();
            // Determine if we need severity question
            if (needsSeverityQuestion(diag)) {
              goTo("injury_severity");
            } else {
              goTo("injury_timeline");
            }
          });
          listEl.appendChild(item);
        });
      }

      if (!hasResults) {
        const empty = document.createElement("div");
        empty.className = "diagnosis-empty";
        empty.textContent = "No matching diagnoses found";
        listEl.appendChild(empty);
      }
    }

    renderList("");
    searchInput.addEventListener("input", () => renderList(searchInput.value));
  }

  function needsSeverityQuestion(diagnosis) {
    const sprain = /sprain/i.test(diagnosis);
    const aclPostOp = /ACL reconstruction/i.test(diagnosis);
    const strain = /strain/i.test(diagnosis);
    return sprain || aclPostOp || strain;
  }

  function renderInjurySeverity(card) {
    const injNum = state.currentInjuryIndex + 1;
    const diag = state.currentInjury.condition || "";

    if (/ACL reconstruction/i.test(diag)) {
      buildQuestion(card, {
        label: `Injury ${injNum} — Severity`,
        title: "What graft type was used?",
        subtitle: "This affects rehab timelines and restrictions."
      });

      buildOptions(card, [
        { value: "BPTB graft", label: "BPTB (bone-patellar tendon-bone)", desc: "Patellar tendon autograft" },
        { value: "Hamstring graft", label: "Hamstring tendon", desc: "Semitendinosus / gracilis autograft" },
        { value: "Quad tendon graft", label: "Quad tendon", desc: "Quadriceps tendon autograft" },
        { value: "Allograft", label: "Allograft", desc: "Donor tissue" },
        { value: "Unknown graft", label: "I'm not sure", desc: "Unknown graft type" }
      ], (value) => {
        state.currentInjury.severity = value;
        goTo("injury_timeline");
      });
    } else {
      // Sprain or strain grading
      buildQuestion(card, {
        label: `Injury ${injNum} — Severity`,
        title: "What grade was it classified as?",
        subtitle: "If you're unsure, choose the closest match."
      });

      buildOptions(card, [
        { value: "Grade 1", label: "Grade 1 — Mild", desc: "Minor stretching, minimal fibre damage" },
        { value: "Grade 2", label: "Grade 2 — Moderate", desc: "Partial tear, some instability" },
        { value: "Grade 3", label: "Grade 3 — Severe", desc: "Complete tear / rupture" },
        { value: "Unknown grade", label: "I'm not sure", desc: "Grade not specified" }
      ], (value) => {
        state.currentInjury.severity = value;
        goTo("injury_timeline");
      });
    }
  }

  function renderInjuryTimeline(card) {
    const injNum = state.currentInjuryIndex + 1;
    const isPostOp = /post-op|reconstruction|repair|surgery/i.test(
      state.currentInjury.condition || ""
    );

    buildQuestion(card, {
      label: `Injury ${injNum} — Timeline`,
      title: isPostOp
        ? "How long ago was your surgery?"
        : "When did this injury happen?",
      subtitle: "This helps determine your rehab phase."
    });

    const options = isPostOp
      ? [
          { value: "0-2 weeks post-op", label: "0-2 weeks", desc: "Very early post-op" },
          { value: "2-6 weeks post-op", label: "2-6 weeks", desc: "Early post-op" },
          { value: "6-12 weeks post-op", label: "6-12 weeks", desc: "Mid-stage rehab" },
          { value: "3-6 months post-op", label: "3-6 months", desc: "Strengthening phase" },
          { value: "6-9 months post-op", label: "6-9 months", desc: "Return to sport prep" },
          { value: "9-12 months post-op", label: "9-12 months", desc: "Late-stage return to sport" },
          { value: "12+ months post-op", label: "12+ months", desc: "Long-term / ongoing" }
        ]
      : [
          { value: "Less than 1 week", label: "Less than 1 week", desc: "Very recent / acute" },
          { value: "1-2 weeks", label: "1-2 weeks", desc: "Recent" },
          { value: "2-6 weeks", label: "2-6 weeks", desc: "Sub-acute" },
          { value: "6-12 weeks", label: "6-12 weeks", desc: "Transitioning" },
          { value: "3-6 months", label: "3-6 months", desc: "Chronic" },
          { value: "6+ months", label: "6+ months", desc: "Long-standing" }
        ];

    buildOptions(card, options, (value) => {
      state.currentInjury.timeline = value;
      goTo("injury_pain");
    });
  }

  function renderInjuryPain(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Pain`,
      title: "What is your current pain level?",
      subtitle: "Rate your average pain on a 0-10 scale."
    });

    let currentVal = 3;
    buildSlider(card, {
      min: 0,
      max: 10,
      step: 1,
      initial: 3,
      label: (v) => {
        if (v === 0) return "0 — No pain";
        if (v <= 3) return `${v} — Mild`;
        if (v <= 6) return `${v} — Moderate`;
        if (v <= 8) return `${v} — Severe`;
        return `${v} — Very severe`;
      },
      leftLabel: "No pain",
      rightLabel: "Worst pain",
      onChange: (v) => { currentVal = v; }
    });

    buildContinueButton(card, "Continue", () => {
      state.currentInjury.pain_level = currentVal;
      goTo("injury_functional");
    });
  }

  function renderInjuryFunctional(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Function`,
      title: "How would you describe your current function?",
      subtitle: "Choose the option that best matches your situation."
    });

    buildOptions(card, [
      {
        value: "Full function, minor discomfort",
        label: "Full function",
        desc: "Can do everything, maybe minor discomfort"
      },
      {
        value: "Mostly functional, some limitations",
        label: "Mostly functional",
        desc: "Some activities limited or modified"
      },
      {
        value: "Moderate limitations, can do daily tasks",
        label: "Moderate limitations",
        desc: "Daily tasks OK, exercise limited"
      },
      {
        value: "Significant limitations, daily tasks affected",
        label: "Significant limitations",
        desc: "Even daily activities are difficult"
      },
      {
        value: "Severe — unable to bear weight or use limb",
        label: "Severe",
        desc: "Cannot bear weight or use the affected area"
      }
    ], (value) => {
      state.currentInjury.functional_level = value;
      goTo("injury_clinician");
    });
  }

  function renderInjuryClinician(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Restrictions`,
      title: "Has a clinician given you specific restrictions?",
      subtitle: "E.g. 'no weight-bearing for 4 weeks', 'avoid overhead pressing'."
    });

    buildOptions(card, [
      { value: "no", label: "No restrictions given", icon: "\u2705" },
      { value: "yes", label: "Yes, I have restrictions", icon: "\uD83D\uDCCB" }
    ], (value) => {
      if (value === "yes") {
        goTo("injury_clinician_text");
      } else {
        state.currentInjury.clinician_restrictions = "None";
        finalizeCurrentInjury();
        goTo("another_injury");
      }
    });
  }

  function renderInjuryClinicianText(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Restrictions`,
      title: "What restrictions were you given?",
      subtitle: "Type them in your own words. Be as specific as possible."
    });

    const textarea = document.createElement("textarea");
    textarea.className = "text-input";
    textarea.rows = 4;
    textarea.placeholder = "E.g. 'No running for 6 weeks', 'Avoid deep knee flexion past 90 degrees'...";
    card.appendChild(textarea);

    buildContinueButton(card, "Continue", () => {
      state.currentInjury.clinician_restrictions = textarea.value.trim() || "None";
      finalizeCurrentInjury();
      goTo("another_injury");
    });
  }

  // -----------------------------------------------------------------
  // FLOW 3B: Undiagnosed
  // -----------------------------------------------------------------

  function renderUndiagRegion(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Location`,
      title: "Where is your pain or problem?",
      subtitle: "Tap the body region."
    });

    const grid = document.createElement("div");
    grid.className = "body-region-grid";

    BODY_REGIONS.forEach((region) => {
      const btn = document.createElement("button");
      btn.className = "body-region-btn";
      btn.innerHTML = `
        <span class="region-icon">${region.icon}</span>
        <span>${region.label}</span>
      `;
      btn.addEventListener("click", () => {
        state.currentInjury.region = region.id;
        goTo("undiag_description");
      });
      grid.appendChild(btn);
    });

    card.appendChild(grid);
  }

  function renderUndiagDescription(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Description`,
      title: "How would you describe the problem?",
      subtitle: "Pick the closest match."
    });

    buildOptions(card, [
      { value: "Sharp pain with specific movements", label: "Sharp pain with specific movements" },
      { value: "Dull ache that's always there", label: "Dull ache that's always there" },
      { value: "Stiffness / tightness", label: "Stiffness or tightness" },
      { value: "Weakness / giving way", label: "Weakness or giving way" },
      { value: "Swelling", label: "Swelling" },
      { value: "Clicking / catching / locking", label: "Clicking, catching, or locking" },
      { value: "Numbness / tingling", label: "Numbness or tingling" }
    ], (value) => {
      state.currentInjury.description = value;
      goTo("undiag_when");
    });
  }

  function renderUndiagWhen(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Triggers`,
      title: "When does it bother you most?",
      subtitle: "Select the primary trigger."
    });

    buildOptions(card, [
      { value: "During exercise only", label: "During exercise only" },
      { value: "After exercise", label: "After exercise" },
      { value: "Morning stiffness", label: "Morning stiffness" },
      { value: "With daily activities", label: "With daily activities (stairs, walking, etc.)" },
      { value: "At rest / at night", label: "At rest or at night" },
      { value: "Constant", label: "It's constant" }
    ], (value) => {
      state.currentInjury.when_bothers = value;
      goTo("undiag_duration");
    });
  }

  function renderUndiagDuration(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Duration`,
      title: "How long have you had this problem?",
      subtitle: null
    });

    buildOptions(card, [
      { value: "Less than 2 weeks", label: "Less than 2 weeks", desc: "Acute" },
      { value: "2-6 weeks", label: "2-6 weeks", desc: "Sub-acute" },
      { value: "6 weeks to 3 months", label: "6 weeks to 3 months", desc: "Transitioning to chronic" },
      { value: "More than 3 months", label: "More than 3 months", desc: "Chronic" }
    ], (value) => {
      state.currentInjury.duration = value;
      goTo("undiag_pain");
    });
  }

  function renderUndiagPain(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Pain`,
      title: "What's the worst your pain has been this week?",
      subtitle: "Rate on a 0-10 scale."
    });

    let currentVal = 4;
    buildSlider(card, {
      min: 0,
      max: 10,
      step: 1,
      initial: 4,
      label: (v) => {
        if (v === 0) return "0 — No pain";
        if (v <= 3) return `${v} — Mild`;
        if (v <= 6) return `${v} — Moderate`;
        if (v <= 8) return `${v} — Severe`;
        return `${v} — Very severe`;
      },
      leftLabel: "No pain",
      rightLabel: "Worst imaginable",
      onChange: (v) => { currentVal = v; }
    });

    buildContinueButton(card, "Continue", () => {
      state.currentInjury.pain_level = currentVal;
      goTo("undiag_impact");
    });
  }

  function renderUndiagImpact(card) {
    const injNum = state.currentInjuryIndex + 1;
    buildQuestion(card, {
      label: `Injury ${injNum} — Impact`,
      title: "How much does it affect your daily life?",
      subtitle: null
    });

    buildOptions(card, [
      { value: "Not at all — only notice it during sport", label: "Not at all", desc: "Only during sport/exercise" },
      { value: "Mildly — I modify some activities", label: "Mildly", desc: "I modify some activities" },
      { value: "Moderately — several daily tasks affected", label: "Moderately", desc: "Several daily tasks affected" },
      { value: "Severely — significant impact on daily life", label: "Severely", desc: "Significant impact on daily life" }
    ], (value) => {
      state.currentInjury.daily_impact = value;
      // Route to a generic protocol based on symptoms
      state.currentInjury.routed_protocol = routeUndiagnosedProtocol(state.currentInjury);
      finalizeCurrentInjury();
      goTo("another_injury");
    });
  }

  function routeUndiagnosedProtocol(injury) {
    const region = injury.region || "";
    const desc = (injury.description || "").toLowerCase();

    if (desc.includes("numbness") || desc.includes("tingling")) {
      return "neurological screening needed";
    }
    if (region === "knee" && desc.includes("giving way")) {
      return "instability management";
    }
    if (desc.includes("sharp pain")) {
      return "pain-dominant management";
    }
    if (desc.includes("stiffness")) {
      return "mobility-focused programme";
    }
    if (desc.includes("weakness")) {
      return "strengthening-focused programme";
    }
    return "generic management";
  }

  // -----------------------------------------------------------------
  // Finalize current injury and ask about another
  // -----------------------------------------------------------------

  function finalizeCurrentInjury() {
    state.injuries.push({ ...state.currentInjury });
    state.currentInjury = {};
    state.currentInjuryIndex++;
  }

  function renderAnotherInjury(card) {
    buildQuestion(card, {
      label: "Injury assessment",
      title: "Do you have another injury to report?",
      subtitle: `You've reported ${state.injuries.length} injury${state.injuries.length > 1 ? " injuries" : ""} so far.`
    });

    // Show summary of injuries reported
    if (state.injuries.length > 0) {
      const summary = document.createElement("div");
      summary.style.marginBottom = "16px";
      state.injuries.forEach((inj, i) => {
        const tag = document.createElement("div");
        tag.className = "injury-tag";
        tag.style.marginBottom = "6px";
        tag.textContent = inj.condition || `${(inj.region || "unknown").charAt(0).toUpperCase() + (inj.region || "unknown").slice(1)} — undiagnosed`;
        summary.appendChild(tag);
      });
      card.appendChild(summary);
    }

    buildOptions(card, [
      { value: "yes", label: "Yes, I have another injury", icon: "\u2795" },
      { value: "no", label: "No, that's all", icon: "\u2705" }
    ], (value) => {
      if (value === "yes") {
        goTo("injury_diagnosed");
      } else {
        // Proceed based on mode
        if (state.answers.mode === "rehab_only") {
          goTo("rehab_days");
        } else if (state.answers.mode === "gym_only") {
          // Gym only with injury — go to red flags
          goTo("redflag_neuro");
        } else {
          // Both mode — go to red flags
          goTo("redflag_neuro");
        }
      }
    });
  }

  // ===================================================================
  // FLOW 4: REHAB-SPECIFIC
  // ===================================================================

  function renderRehabDays(card) {
    buildQuestion(card, {
      label: "Rehab profile",
      title: "How many days per week can you dedicate to rehab?",
      subtitle: "Consistency is more important than frequency."
    });

    buildOptions(card, [
      { value: 2, label: "2 days" },
      { value: 3, label: "3 days" },
      { value: 4, label: "4 days" },
      { value: 5, label: "5 days" },
      { value: 6, label: "6 days" },
      { value: 7, label: "7 days (daily)" }
    ], (value) => {
      state.answers.days_per_week = value;
      goTo("rehab_session_length");
    }, { gridClass: "three-col" });
  }

  function renderRehabSessionLength(card) {
    buildQuestion(card, {
      label: "Rehab profile",
      title: "How long can each rehab session be?",
      subtitle: null
    });

    buildOptions(card, [
      { value: 15, label: "15 minutes", desc: "Quick HEP" },
      { value: 20, label: "20 minutes", desc: "Standard home programme" },
      { value: 30, label: "30 minutes", desc: "Full session" },
      { value: 45, label: "45 minutes", desc: "Extended session" },
      { value: 60, label: "60 minutes", desc: "Comprehensive" }
    ], (value) => {
      state.answers.session_minutes = value;
      goTo("rehab_equipment");
    }, { gridClass: "three-col" });
  }

  function renderRehabEquipment(card) {
    buildQuestion(card, {
      label: "Rehab profile",
      title: "What equipment do you have for rehab?",
      subtitle: null
    });

    buildOptions(card, [
      {
        value: "full_gym",
        label: "Full gym",
        icon: "\uD83C\uDFCB\uFE0F",
        desc: "Access to a gym with all equipment"
      },
      {
        value: "basic_gym",
        label: "Basic gym / physio clinic",
        icon: "\uD83C\uDFE5",
        desc: "Some machines, dumbbells, bands"
      },
      {
        value: "home_db_bands",
        label: "Home — DBs & bands",
        icon: "\uD83C\uDFE1",
        desc: "Dumbbells and resistance bands at home"
      },
      {
        value: "minimal",
        label: "Minimal / bodyweight",
        icon: "\uD83E\uDDD8",
        desc: "Just your body, maybe a towel"
      }
    ], (value) => {
      state.answers.equipment = value;
      goTo("rehab_seeing_physio");
    });
  }

  function renderRehabSeeingPhysio(card) {
    buildQuestion(card, {
      label: "Rehab profile",
      title: "Are you currently seeing a physiotherapist?",
      subtitle: "This helps us know how to frame the programme."
    });

    buildOptions(card, [
      { value: "Yes — actively seeing one", label: "Yes, I'm seeing a physio", icon: "\uD83D\uDC68\u200D\u2695\uFE0F" },
      { value: "Previously but not currently", label: "Previously, but not anymore", icon: "\u23F0" },
      { value: "No", label: "No", icon: "\u274C" }
    ], (value) => {
      state.answers.seeing_physio = value;
      goTo("rehab_previous");
    });
  }

  function renderRehabPrevious(card) {
    buildQuestion(card, {
      label: "Rehab profile",
      title: "Have you done rehab exercises before for this condition?",
      subtitle: null
    });

    buildOptions(card, [
      { value: "Yes, completed a full programme", label: "Yes, completed a full programme", desc: "Finished a course of rehab" },
      { value: "Yes, but didn't finish", label: "Started but didn't finish", desc: "Began rehab but dropped off" },
      { value: "Yes, currently doing some", label: "Currently doing some exercises", desc: "Already have a HEP" },
      { value: "No, this is my first time", label: "No, never done rehab", desc: "Starting fresh" }
    ], (value) => {
      state.answers.previous_rehab = value;
      goTo("redflag_neuro");
    });
  }

  // ===================================================================
  // FLOW 5: RED FLAG SCREENING
  // ===================================================================

  function renderRedFlagNeuro(card) {
    buildQuestion(card, {
      label: "Safety screening",
      title: "Are you experiencing any of the following neurological symptoms?",
      subtitle: "Select all that apply, or 'None of these'."
    });

    const options = [
      { value: "numbness_legs", label: "Numbness or tingling in legs/feet" },
      { value: "numbness_arms", label: "Numbness or tingling in arms/hands" },
      { value: "weakness_sudden", label: "Sudden unexplained weakness in a limb" },
      { value: "bladder_bowel", label: "Loss of bladder or bowel control" },
      { value: "balance_problems", label: "Balance problems or difficulty walking" },
      { value: "saddle_numbness", label: "Numbness in saddle area (groin/buttocks)" }
    ];

    let selected = [];

    const grid = buildOptions(card, options, (value, btn) => {
      if (selected.includes(value)) {
        selected = selected.filter((v) => v !== value);
        btn.classList.remove("selected");
      } else {
        selected.push(value);
        btn.classList.add("selected");
        // Deselect "none"
        const noneBtn = grid.querySelector('[data-value="none"]');
        if (noneBtn) noneBtn.classList.remove("selected");
        selected = selected.filter((v) => v !== "none");
      }
    });

    // "None" option
    const noneOpt = document.createElement("button");
    noneOpt.className = "option-btn";
    noneOpt.setAttribute("data-value", "none");
    noneOpt.innerHTML = `<span class="option-icon">\u2705</span><span class="option-text"><span class="option-title">None of these</span></span>`;
    noneOpt.addEventListener("click", () => {
      selected = ["none"];
      grid.querySelectorAll(".option-btn").forEach((b) => b.classList.remove("selected"));
      noneOpt.classList.add("selected");
    });
    grid.appendChild(noneOpt);

    buildContinueButton(card, "Continue", () => {
      if (selected.length === 0) {
        selected = ["none"];
      }
      state.answers.redflag_neuro = selected;
      goTo("redflag_symptoms");
    });
  }

  function renderRedFlagSymptoms(card) {
    buildQuestion(card, {
      label: "Safety screening",
      title: "Have you experienced any of these recently?",
      subtitle: "Select all that apply, or 'None of these'."
    });

    const options = [
      { value: "chest_pain", label: "Chest pain during exercise" },
      { value: "unexplained_weight_loss", label: "Unexplained weight loss" },
      { value: "fever_night_sweats", label: "Fever or night sweats" },
      { value: "severe_unrelenting_pain", label: "Severe, unrelenting pain (not relieved by rest)" },
      { value: "recent_trauma", label: "Recent significant trauma (fall, collision)" },
      { value: "pain_worsening", label: "Pain that is progressively worsening despite rest" }
    ];

    let selected = [];

    const grid = buildOptions(card, options, (value, btn) => {
      if (selected.includes(value)) {
        selected = selected.filter((v) => v !== value);
        btn.classList.remove("selected");
      } else {
        selected.push(value);
        btn.classList.add("selected");
        const noneBtn = grid.querySelector('[data-value="none"]');
        if (noneBtn) noneBtn.classList.remove("selected");
        selected = selected.filter((v) => v !== "none");
      }
    });

    const noneOpt = document.createElement("button");
    noneOpt.className = "option-btn";
    noneOpt.setAttribute("data-value", "none");
    noneOpt.innerHTML = `<span class="option-icon">\u2705</span><span class="option-text"><span class="option-title">None of these</span></span>`;
    noneOpt.addEventListener("click", () => {
      selected = ["none"];
      grid.querySelectorAll(".option-btn").forEach((b) => b.classList.remove("selected"));
      noneOpt.classList.add("selected");
    });
    grid.appendChild(noneOpt);

    buildContinueButton(card, "Continue", () => {
      if (selected.length === 0) {
        selected = ["none"];
      }
      state.answers.redflag_symptoms = selected;
      goTo("redflag_medical");
    });
  }

  function renderRedFlagMedical(card) {
    buildQuestion(card, {
      label: "Safety screening",
      title: "Do you have any of these medical conditions?",
      subtitle: "Select all that apply, or 'None of these'."
    });

    const options = [
      { value: "cancer_history", label: "History of cancer" },
      { value: "infection_recent", label: "Recent infection or illness" },
      { value: "heart_condition", label: "Heart condition" },
      { value: "osteoporosis", label: "Osteoporosis" },
      { value: "blood_thinners", label: "On blood thinners / anticoagulants" },
      { value: "autoimmune", label: "Autoimmune condition" },
      { value: "diabetes", label: "Diabetes" }
    ];

    let selected = [];

    const grid = buildOptions(card, options, (value, btn) => {
      if (selected.includes(value)) {
        selected = selected.filter((v) => v !== value);
        btn.classList.remove("selected");
      } else {
        selected.push(value);
        btn.classList.add("selected");
        const noneBtn = grid.querySelector('[data-value="none"]');
        if (noneBtn) noneBtn.classList.remove("selected");
        selected = selected.filter((v) => v !== "none");
      }
    });

    const noneOpt = document.createElement("button");
    noneOpt.className = "option-btn";
    noneOpt.setAttribute("data-value", "none");
    noneOpt.innerHTML = `<span class="option-icon">\u2705</span><span class="option-text"><span class="option-title">None of these</span></span>`;
    noneOpt.addEventListener("click", () => {
      selected = ["none"];
      grid.querySelectorAll(".option-btn").forEach((b) => b.classList.remove("selected"));
      noneOpt.classList.add("selected");
    });
    grid.appendChild(noneOpt);

    buildContinueButton(card, "Complete screening", () => {
      if (selected.length === 0) {
        selected = ["none"];
      }
      state.answers.redflag_medical = selected;

      // Check for red flags
      const redFlagResult = evaluateRedFlags();
      if (redFlagResult) {
        state.redFlagTriggered = redFlagResult;
        goTo("redflag_block");
      } else {
        // Mark osteoporosis flag if selected
        if (selected.includes("osteoporosis")) {
          state.answers.osteoporosis_flag = true;
        }
        finishOnboarding();
      }
    });
  }

  // -----------------------------------------------------------------
  // Red flag evaluation
  // -----------------------------------------------------------------

  function evaluateRedFlags() {
    const neuro = state.answers.redflag_neuro || [];
    const symptoms = state.answers.redflag_symptoms || [];
    const medical = state.answers.redflag_medical || [];
    const hasSpineInjury = state.injuries.some(
      (inj) => (inj.region || "").toLowerCase() === "spine"
    );

    // URGENT: Bladder/bowel loss — cauda equina risk
    if (neuro.includes("bladder_bowel") || neuro.includes("saddle_numbness")) {
      return {
        level: "URGENT",
        title: "Urgent Medical Attention Required",
        message:
          "Loss of bladder/bowel control or saddle area numbness may indicate <strong>cauda equina syndrome</strong>, a medical emergency. " +
          "Please <strong>go to your nearest emergency department immediately</strong>. Do not proceed with any exercise programme.",
        icon: "\uD83D\uDEA8",
        allowProceed: false
      };
    }

    // SERIOUS: Numbness + spine injury
    if (
      (neuro.includes("numbness_legs") || neuro.includes("numbness_arms")) &&
      hasSpineInjury
    ) {
      return {
        level: "SERIOUS",
        title: "Medical Review Needed",
        message:
          "You report numbness/tingling alongside a spinal condition. This combination requires <strong>medical assessment before starting an exercise programme</strong>. " +
          "Please see your GP or physiotherapist for a neurological examination before proceeding.",
        icon: "\u26A0\uFE0F",
        allowProceed: false
      };
    }

    // Chest pain
    if (symptoms.includes("chest_pain")) {
      return {
        level: "GP",
        title: "GP Assessment Recommended",
        message:
          "Chest pain during exercise needs to be <strong>assessed by a GP</strong> before starting a training programme. " +
          "This is likely nothing serious, but it's important to rule out cardiac causes before we proceed.",
        icon: "\uD83D\uDC9A",
        allowProceed: false
      };
    }

    // Unexplained weight loss + fever
    if (
      symptoms.includes("unexplained_weight_loss") &&
      symptoms.includes("fever_night_sweats")
    ) {
      return {
        level: "INVESTIGATION",
        title: "Medical Investigation Recommended",
        message:
          "Unexplained weight loss combined with fever/night sweats warrants <strong>further medical investigation</strong>. " +
          "Please see your GP for appropriate tests before beginning a training programme.",
        icon: "\uD83D\uDD0D",
        allowProceed: false
      };
    }

    // Cancer, infection, or heart condition
    if (
      medical.includes("cancer_history") ||
      medical.includes("infection_recent") ||
      medical.includes("heart_condition")
    ) {
      return {
        level: "CLEARANCE",
        title: "Medical Clearance Required",
        message:
          "Given your medical history, we recommend getting <strong>medical clearance from your GP or specialist</strong> before starting this programme. " +
          "Once cleared, come back and we'll build your plan. " +
          "This is a safety precaution, not a barrier — many people with these conditions train successfully with appropriate guidance.",
        icon: "\uD83D\uDCCB",
        allowProceed: false
      };
    }

    // Osteoporosis — flag but allow
    // (handled in the caller — not a blocking red flag)

    return null;
  }

  function renderRedFlagBlock(card) {
    const rf = state.redFlagTriggered;
    if (!rf) return;

    // Replace with full-screen
    containerEl.innerHTML = "";
    const screen = document.createElement("div");
    screen.className = "red-flag-screen";

    screen.innerHTML = `
      <div class="rf-icon">${rf.icon}</div>
      <div class="rf-title" style="color: var(--error);">${rf.title}</div>
      <div class="rf-message">${rf.message}</div>
    `;

    const actionRow = document.createElement("div");
    actionRow.className = "action-row center";

    if (onRedFlag) {
      const saveBtn = document.createElement("button");
      saveBtn.className = "btn btn-secondary";
      saveBtn.textContent = "Save my profile for later";
      saveBtn.addEventListener("click", () => {
        onRedFlag(collectProfile(), rf);
      });
      actionRow.appendChild(saveBtn);
    }

    const restartBtn = document.createElement("button");
    restartBtn.className = "btn btn-ghost";
    restartBtn.textContent = "Start over";
    restartBtn.addEventListener("click", () => {
      init(containerEl, { onComplete, onRedFlag });
    });
    actionRow.appendChild(restartBtn);

    screen.appendChild(actionRow);
    containerEl.appendChild(screen);
  }

  // ===================================================================
  // COMPLETION
  // ===================================================================

  function finishOnboarding() {
    const profile = collectProfile();
    if (onComplete) {
      onComplete(profile);
    }
  }

  function collectProfile() {
    const profile = {
      goal: state.answers.goal || "general_fitness",
      mode: state.answers.mode || "gym_only",
      days_per_week: state.answers.days_per_week || 4,
      session_minutes: state.answers.session_minutes || 60,
      experience: state.answers.experience || "intermediate",
      equipment: state.answers.equipment || "full_gym",
      injuries: state.injuries.map((inj) => {
        if (inj.diagnosed) {
          return {
            diagnosed: true,
            condition: inj.condition || "Unknown",
            region: inj.region || "unknown",
            severity: inj.severity || "Not specified",
            timeline: inj.timeline || "Not specified",
            pain_level: inj.pain_level != null ? inj.pain_level : "Not specified",
            functional_level: inj.functional_level || "Not specified",
            clinician_restrictions: inj.clinician_restrictions || "None"
          };
        } else {
          return {
            diagnosed: false,
            region: inj.region || "unknown",
            description: inj.description || "",
            when_bothers: inj.when_bothers || "",
            duration: inj.duration || "",
            pain_level: inj.pain_level != null ? inj.pain_level : "",
            daily_impact: inj.daily_impact || "",
            routed_protocol: inj.routed_protocol || "generic management"
          };
        }
      })
    };

    // Both mode extras
    if (state.answers.mode === "both") {
      profile.dedicated_rehab_days = state.answers.dedicated_rehab_days || "No";
      profile.gym_sessions = state.answers.gym_sessions || state.answers.days_per_week;
      profile.rehab_sessions = state.answers.rehab_sessions || 0;
      profile.priority_slider = state.answers.priority_slider || "50/50";
    }

    // Rehab only extras
    if (state.answers.mode === "rehab_only") {
      profile.seeing_physio = state.answers.seeing_physio || "Unknown";
      profile.previous_rehab = state.answers.previous_rehab || "None";
    }

    // Red flag data — convert array-based answers to backend's boolean object format
    const neuro = state.answers.redflag_neuro || [];
    const symptoms = state.answers.redflag_symptoms || [];
    const medical = state.answers.redflag_medical || [];

    const hasAnyRedFlag =
      (neuro.length > 0 && !neuro.includes("none")) ||
      (symptoms.length > 0 && !symptoms.includes("none")) ||
      (medical.length > 0 && !medical.includes("none"));

    if (hasAnyRedFlag) {
      profile.red_flags = {
        numbness_tingling: neuro.includes("numbness_arms") || neuro.includes("saddle_numbness"),
        weakness: neuro.includes("weakness_sudden"),
        bladder_bowel: neuro.includes("bladder_bowel"),
        chest_pain: symptoms.includes("chest_pain"),
        weight_loss: symptoms.includes("unexplained_weight_loss"),
        fever: symptoms.includes("fever_night_sweats"),
        fall_collision: symptoms.includes("recent_trauma"),
        osteoporosis: medical.includes("osteoporosis"),
        cancer: medical.includes("cancer_history"),
        infection: medical.includes("infection_recent"),
        heart_condition: medical.includes("heart_condition")
      };
    }

    return profile;
  }

  // ===================================================================
  // Public API
  // ===================================================================

  return {
    init,
    getProgress,
    getState: () => ({ ...state }),
    collectProfile
  };
})();
