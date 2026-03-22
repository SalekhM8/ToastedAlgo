/* ===================================================================
   TOASTED — Plan Display Module
   Renders the generated training plan with collapsible day cards,
   honesty verdict, validation, and grading results.
   =================================================================== */

const PlanDisplay = (() => {
  "use strict";

  let containerEl = null;
  let planData = null;
  let validationData = null;
  let gradingData = null;
  let callbacks = {};

  // Chevron SVG (shared)
  const CHEVRON_SVG = `<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`;

  // -----------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------

  function init(container, plan, opts = {}) {
    containerEl = container;
    planData = plan;
    validationData = opts.validation || null;
    gradingData = opts.grading || null;
    callbacks = {
      onNewPlan: opts.onNewPlan || null,
      onGradePlan: opts.onGradePlan || null
    };
    render();
  }

  function updateGrading(grading) {
    gradingData = grading;
    render();
  }

  function updateValidation(validation) {
    validationData = validation;
    render();
  }

  // -----------------------------------------------------------------
  // Main render
  // -----------------------------------------------------------------

  function render() {
    if (!containerEl || !planData) return;
    containerEl.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.className = "plan-wrapper";

    // Toolbar
    wrapper.appendChild(renderToolbar());

    // Plan header
    wrapper.appendChild(renderPlanHeader());

    // Honesty verdict
    if (planData.honestyVerdict) {
      wrapper.appendChild(renderHonestyVerdict(planData.honestyVerdict));
    }

    // Warnings
    if (planData.warnings && planData.warnings.length > 0) {
      wrapper.appendChild(renderWarnings(planData.warnings));
    }

    // Day cards
    if (planData.days && planData.days.length > 0) {
      const daysSection = document.createElement("div");
      daysSection.style.marginBottom = "20px";

      const daysTitle = document.createElement("h3");
      daysTitle.style.cssText = "font-size: 1.1rem; font-weight: 700; margin-bottom: 12px; color: var(--text-secondary);";
      daysTitle.textContent = "Weekly Programme";
      daysSection.appendChild(daysTitle);

      planData.days.forEach((day, i) => {
        daysSection.appendChild(renderDayCard(day, i === 0));
      });

      wrapper.appendChild(daysSection);
    }

    // Home sessions
    if (planData.homeSessions) {
      wrapper.appendChild(renderHomeSessions(planData.homeSessions));
    }

    // Deload instructions
    if (planData.deloadInstructions) {
      wrapper.appendChild(
        renderCollapsibleSection("Deload Instructions", planData.deloadInstructions)
      );
    }

    // Progression guidance
    if (planData.progressionGuidance) {
      wrapper.appendChild(
        renderCollapsibleSection("Progression Guidance", planData.progressionGuidance)
      );
    }

    // Validation results
    if (validationData) {
      wrapper.appendChild(renderValidation(validationData));
    }

    // Grading results
    if (gradingData) {
      wrapper.appendChild(renderGrading(gradingData));
    }

    containerEl.appendChild(wrapper);
  }

  // -----------------------------------------------------------------
  // Toolbar
  // -----------------------------------------------------------------

  function renderToolbar() {
    const toolbar = document.createElement("div");
    toolbar.className = "plan-toolbar";

    const left = document.createElement("div");
    left.className = "plan-toolbar-left";
    const logo = document.createElement("div");
    logo.innerHTML = `<span style="font-size: 1.3rem; font-weight: 800; letter-spacing: -0.03em;"><span style="color: var(--primary);">Toasted</span> Plan</span>`;
    left.appendChild(logo);
    toolbar.appendChild(left);

    const right = document.createElement("div");
    right.className = "plan-toolbar-right";

    if (callbacks.onGradePlan) {
      const gradeBtn = document.createElement("button");
      gradeBtn.className = "btn btn-secondary btn-sm";
      gradeBtn.textContent = gradingData ? "Re-grade Plan" : "Grade This Plan";
      gradeBtn.addEventListener("click", () => callbacks.onGradePlan(planData));
      right.appendChild(gradeBtn);
    }

    if (callbacks.onNewPlan) {
      const newBtn = document.createElement("button");
      newBtn.className = "btn btn-primary btn-sm";
      newBtn.textContent = "Generate New Plan";
      newBtn.addEventListener("click", callbacks.onNewPlan);
      right.appendChild(newBtn);
    }

    toolbar.appendChild(right);
    return toolbar;
  }

  // -----------------------------------------------------------------
  // Plan Header
  // -----------------------------------------------------------------

  function renderPlanHeader() {
    const header = planData.planHeader || {};
    const card = document.createElement("div");
    card.className = "plan-header";

    const title = document.createElement("div");
    title.className = "plan-title";
    const goalLabel = formatGoal(header.goal);
    const modeLabel = formatMode(header.mode);
    title.innerHTML = `<span>${goalLabel}</span> Programme`;
    card.appendChild(title);

    const modeNote = document.createElement("div");
    modeNote.style.cssText = "font-size: 0.85rem; color: var(--text-secondary); margin-top: 2px;";
    modeNote.textContent = modeLabel;
    card.appendChild(modeNote);

    // Meta items
    const meta = document.createElement("div");
    meta.className = "plan-meta";

    const metaItems = [
      { icon: "\uD83D\uDCC5", label: "Days", value: header.daysPerWeek ? `${header.daysPerWeek}/week` : "N/A" },
      { icon: "\u23F1\uFE0F", label: "Session", value: header.sessionMinutes ? `${header.sessionMinutes} min` : "N/A" },
      { icon: "\uD83C\uDF1F", label: "Experience", value: capitalize(header.experience || "N/A") },
      { icon: "\uD83C\uDFCB\uFE0F", label: "Equipment", value: formatEquipment(header.equipment) }
    ];

    metaItems.forEach((item) => {
      const el = document.createElement("div");
      el.className = "plan-meta-item";
      el.innerHTML = `<span class="meta-icon">${item.icon}</span> <span class="detail-label">${item.label}:</span> <span class="meta-value">${item.value}</span>`;
      meta.appendChild(el);
    });

    card.appendChild(meta);

    // Injuries
    if (header.injuries && header.injuries.length > 0) {
      const injList = document.createElement("div");
      injList.className = "plan-injuries-list";
      header.injuries.forEach((inj) => {
        const tag = document.createElement("span");
        tag.className = "injury-tag";
        let label = inj.condition || "Unknown";
        if (inj.severity) label += ` (${inj.severity})`;
        if (inj.phase) label += ` \u2014 ${inj.phase}`;
        tag.textContent = label;
        injList.appendChild(tag);
      });
      card.appendChild(injList);
    }

    return card;
  }

  // -----------------------------------------------------------------
  // Honesty Verdict
  // -----------------------------------------------------------------

  function renderHonestyVerdict(verdict) {
    const el = document.createElement("div");
    const viability = verdict.goalViability || "genuine";
    el.className = `honesty-verdict ${viability}`;

    const labelMap = {
      genuine: "Goal Assessment: Viable",
      partial: "Goal Assessment: Partially Viable",
      not_viable: "Goal Assessment: Not Viable As Stated"
    };

    el.innerHTML = `
      <div class="verdict-label">${labelMap[viability] || "Goal Assessment"}</div>
      <div class="verdict-message">${escapeHtml(verdict.message || "")}</div>
    `;

    return el;
  }

  // -----------------------------------------------------------------
  // Warnings
  // -----------------------------------------------------------------

  function renderWarnings(warnings) {
    const section = document.createElement("div");
    section.className = "warnings-section";

    warnings.forEach((w) => {
      const item = document.createElement("div");
      item.className = "warning-item";
      item.innerHTML = `<span class="warning-icon">\u26A0\uFE0F</span><span>${escapeHtml(w)}</span>`;
      section.appendChild(item);
    });

    return section;
  }

  // -----------------------------------------------------------------
  // Day Card
  // -----------------------------------------------------------------

  function renderDayCard(day, openByDefault = false) {
    const card = document.createElement("div");
    card.className = "day-card" + (openByDefault ? " open" : "");

    // Header
    const header = document.createElement("div");
    header.className = "day-card-header";

    const headerLeft = document.createElement("div");
    headerLeft.className = "day-card-header-left";

    const dayNum = document.createElement("div");
    dayNum.className = "day-number";
    dayNum.textContent = day.dayNumber || "?";
    headerLeft.appendChild(dayNum);

    const titleWrap = document.createElement("div");
    const dayTitle = document.createElement("div");
    dayTitle.className = "day-title";
    dayTitle.textContent = day.title || `Day ${day.dayNumber}`;
    titleWrap.appendChild(dayTitle);

    if (day.dayType) {
      const daySub = document.createElement("div");
      daySub.className = "day-subtitle";
      daySub.textContent = day.dayType;
      titleWrap.appendChild(daySub);
    }
    headerLeft.appendChild(titleWrap);
    header.appendChild(headerLeft);

    const headerRight = document.createElement("div");
    headerRight.className = "day-card-header-right";

    if (day.intensityLevel) {
      const badge = document.createElement("span");
      badge.className = `intensity-badge ${day.intensityLevel}`;
      badge.textContent = day.intensityLevel;
      headerRight.appendChild(badge);
    }

    if (day.estimatedMinutes) {
      const timeBadge = document.createElement("span");
      timeBadge.className = "time-badge";
      timeBadge.textContent = `${day.estimatedMinutes} min`;
      headerRight.appendChild(timeBadge);
    }

    headerRight.insertAdjacentHTML("beforeend", CHEVRON_SVG);
    header.appendChild(headerRight);

    header.addEventListener("click", () => {
      card.classList.toggle("open");
    });

    card.appendChild(header);

    // Body
    const body = document.createElement("div");
    body.className = "day-card-body";
    const bodyInner = document.createElement("div");
    bodyInner.className = "day-card-body-inner";

    if (day.blocks && day.blocks.length > 0) {
      day.blocks.forEach((block) => {
        bodyInner.appendChild(renderExerciseBlock(block));
      });
    }

    body.appendChild(bodyInner);
    card.appendChild(body);

    return card;
  }

  // -----------------------------------------------------------------
  // Exercise Block
  // -----------------------------------------------------------------

  function renderExerciseBlock(block) {
    const el = document.createElement("div");
    el.className = `exercise-block ${block.blockType || ""}`;

    // Block header
    const header = document.createElement("div");
    header.className = "block-header";

    const label = document.createElement("div");
    label.className = "block-label";
    label.textContent = block.blockLabel || formatBlockType(block.blockType);
    header.appendChild(label);

    if (block.estimatedMinutes) {
      const time = document.createElement("div");
      time.className = "block-time";
      time.textContent = `~${block.estimatedMinutes} min`;
      header.appendChild(time);
    }

    el.appendChild(header);

    // Exercise rows
    if (block.exercises && block.exercises.length > 0) {
      block.exercises.forEach((ex) => {
        el.appendChild(renderExerciseRow(ex));
      });
    }

    return el;
  }

  // -----------------------------------------------------------------
  // Exercise Row
  // -----------------------------------------------------------------

  function renderExerciseRow(ex) {
    const row = document.createElement("div");
    row.className = "exercise-row";

    // Left: name + details
    const leftCol = document.createElement("div");

    const nameEl = document.createElement("div");
    nameEl.className = "exercise-name";
    nameEl.textContent = ex.name || "Unknown exercise";
    leftCol.appendChild(nameEl);

    const details = document.createElement("div");
    details.className = "exercise-details";

    // Sets x Reps
    if (ex.sets && ex.reps) {
      details.appendChild(makeDetailTag(`${ex.sets} \u00D7 ${ex.reps}`));
    }

    // RPE
    if (ex.rpe != null) {
      const rpe = document.createElement("span");
      rpe.className = "rpe-badge " + getRpeClass(ex.rpe);
      rpe.textContent = `RPE ${ex.rpe}`;
      details.appendChild(rpe);
    }

    // Rest
    if (ex.restSeconds) {
      details.appendChild(makeDetailTag(`${ex.restSeconds}s rest`, "Rest"));
    }

    // Tempo
    if (ex.tempo) {
      details.appendChild(makeDetailTag(ex.tempo, "Tempo"));
    }

    leftCol.appendChild(details);
    row.appendChild(leftCol);

    // Right: purpose badge
    if (ex.purpose) {
      const purpose = document.createElement("span");
      purpose.className = `exercise-purpose ${ex.purpose}`;
      purpose.textContent = ex.purpose.toUpperCase();
      row.appendChild(purpose);
    }

    // Dose notes (full width)
    if (ex.doseNotes) {
      const notes = document.createElement("div");
      notes.className = "exercise-notes";
      notes.textContent = ex.doseNotes;
      row.appendChild(notes);
    }

    // Substitution note (full width)
    if (ex.substitutionNote) {
      const sub = document.createElement("div");
      sub.className = "exercise-substitution";
      sub.textContent = "\u21AA " + ex.substitutionNote;
      row.appendChild(sub);
    }

    return row;
  }

  function makeDetailTag(text, labelPrefix) {
    const tag = document.createElement("span");
    tag.className = "exercise-detail-tag";
    if (labelPrefix) {
      tag.innerHTML = `<span class="detail-label">${labelPrefix}:</span> ${escapeHtml(text)}`;
    } else {
      tag.textContent = text;
    }
    return tag;
  }

  function getRpeClass(rpe) {
    if (rpe <= 5) return "rpe-low";
    if (rpe <= 7) return "rpe-mid";
    return "rpe-high";
  }

  // -----------------------------------------------------------------
  // Home Sessions
  // -----------------------------------------------------------------

  function renderHomeSessions(homeSessions) {
    const card = document.createElement("div");
    card.className = "home-sessions-card";

    const title = document.createElement("div");
    title.className = "section-title";
    title.textContent = "Home Rehab Sessions";
    card.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "section-meta";
    meta.textContent = `${homeSessions.frequencyPerWeek || "?"}\u00D7/week \u00B7 ${homeSessions.durationMinutes || "?"} minutes each`;
    card.appendChild(meta);

    if (homeSessions.exercises && homeSessions.exercises.length > 0) {
      const block = document.createElement("div");
      block.className = "exercise-block rehab_warmup";
      block.style.borderLeftColor = "var(--success)";

      const blockHeader = document.createElement("div");
      blockHeader.className = "block-header";
      blockHeader.innerHTML = `<div class="block-label" style="color: var(--success);">Home Exercises</div>`;
      block.appendChild(blockHeader);

      homeSessions.exercises.forEach((ex) => {
        const row = document.createElement("div");
        row.className = "exercise-row";

        const leftCol = document.createElement("div");
        const nameEl = document.createElement("div");
        nameEl.className = "exercise-name";
        nameEl.textContent = ex.name || "Unknown";
        leftCol.appendChild(nameEl);

        const details = document.createElement("div");
        details.className = "exercise-details";

        if (ex.sets && ex.reps) {
          details.appendChild(makeDetailTag(`${ex.sets} \u00D7 ${ex.reps}`));
        }
        if (ex.rpe != null) {
          const rpe = document.createElement("span");
          rpe.className = "rpe-badge " + getRpeClass(ex.rpe);
          rpe.textContent = `RPE ${ex.rpe}`;
          details.appendChild(rpe);
        }

        leftCol.appendChild(details);
        row.appendChild(leftCol);

        if (ex.purpose) {
          const purpose = document.createElement("span");
          purpose.className = `exercise-purpose rehab`;
          purpose.textContent = ex.purpose.toUpperCase();
          row.appendChild(purpose);
        }

        block.appendChild(row);
      });

      card.appendChild(block);
    }

    return card;
  }

  // -----------------------------------------------------------------
  // Collapsible Section
  // -----------------------------------------------------------------

  function renderCollapsibleSection(titleText, content) {
    const section = document.createElement("div");
    section.className = "collapsible-section";

    const header = document.createElement("div");
    header.className = "collapsible-header";
    header.innerHTML = `
      <span class="section-title">${escapeHtml(titleText)}</span>
      ${CHEVRON_SVG}
    `;
    header.addEventListener("click", () => {
      section.classList.toggle("open");
    });
    section.appendChild(header);

    const body = document.createElement("div");
    body.className = "collapsible-body";
    const inner = document.createElement("div");
    inner.className = "collapsible-body-inner";
    inner.textContent = content;
    body.appendChild(inner);
    section.appendChild(body);

    return section;
  }

  // -----------------------------------------------------------------
  // Validation Results
  // -----------------------------------------------------------------

  function renderValidation(validation) {
    const section = document.createElement("div");
    section.className = "validation-section";

    const title = document.createElement("div");
    title.className = "section-title";
    title.textContent = "Validation Results";
    section.appendChild(title);

    const items = [];

    if (validation.errors && validation.errors.length > 0) {
      validation.errors.forEach((err) => {
        items.push({
          type: "error",
          icon: "\u274C",
          text: err.reason || err.type || "Validation error"
        });
      });
    }

    if (validation.warnings && validation.warnings.length > 0) {
      validation.warnings.forEach((warn) => {
        items.push({
          type: "warning",
          icon: "\u26A0\uFE0F",
          text: warn.reason || warn.type || "Warning"
        });
      });
    }

    if (items.length === 0) {
      items.push({
        type: "pass",
        icon: "\u2705",
        text: "All validation checks passed"
      });
    }

    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = `validation-item v-${item.type}`;
      row.innerHTML = `<span class="v-icon">${item.icon}</span><span class="v-text">${escapeHtml(item.text)}</span>`;
      section.appendChild(row);
    });

    // Summary count
    const errorCount = (validation.errors || []).length;
    const warnCount = (validation.warnings || []).length;
    if (errorCount > 0 || warnCount > 0) {
      const summary = document.createElement("div");
      summary.style.cssText = "margin-top: 12px; font-size: 0.8rem; color: var(--text-muted);";
      const parts = [];
      if (errorCount > 0) parts.push(`${errorCount} error${errorCount > 1 ? "s" : ""}`);
      if (warnCount > 0) parts.push(`${warnCount} warning${warnCount > 1 ? "s" : ""}`);
      summary.textContent = parts.join(", ");
      section.appendChild(summary);
    }

    return section;
  }

  // -----------------------------------------------------------------
  // Grading Results
  // -----------------------------------------------------------------

  function renderGrading(grading) {
    const section = document.createElement("div");
    section.className = "grading-section";

    const title = document.createElement("div");
    title.className = "section-title";
    title.textContent = "Plan Grading";
    section.appendChild(title);

    // Overall score
    if (grading.overall_score != null) {
      const overall = document.createElement("div");
      overall.className = "grading-overall";
      const score = grading.overall_score;
      let color = "var(--success)";
      if (score < 50) color = "var(--error)";
      else if (score < 75) color = "var(--warning)";
      overall.style.color = color;
      overall.textContent = `${score}/100`;
      section.appendChild(overall);
    }

    // Grade label
    if (grading.grade) {
      const gradeLabel = document.createElement("div");
      gradeLabel.style.cssText = "font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 16px;";
      gradeLabel.textContent = `Grade: ${grading.grade}`;
      section.appendChild(gradeLabel);
    }

    // Criteria breakdown
    if (grading.criteria && typeof grading.criteria === "object") {
      const criteriaWrap = document.createElement("div");
      criteriaWrap.className = "grading-criteria";

      const criteriaEntries = Object.entries(grading.criteria);
      criteriaEntries.forEach(([key, value]) => {
        const score = typeof value === "object" ? (value.score || value.value || 0) : value;
        const maxScore = typeof value === "object" ? (value.max || 100) : 100;
        const pct = (score / maxScore) * 100;

        let barColor = "var(--success)";
        if (pct < 50) barColor = "var(--error)";
        else if (pct < 75) barColor = "var(--warning)";

        const row = document.createElement("div");
        row.className = "grading-criterion";

        const label = document.createElement("div");
        label.className = "criterion-label";
        label.textContent = formatCriterionLabel(key);
        row.appendChild(label);

        const barBg = document.createElement("div");
        barBg.className = "criterion-bar-bg";
        const barFill = document.createElement("div");
        barFill.className = "criterion-bar-fill";
        barFill.style.width = `${pct}%`;
        barFill.style.background = barColor;
        barBg.appendChild(barFill);
        row.appendChild(barBg);

        const scoreEl = document.createElement("div");
        scoreEl.className = "criterion-score";
        scoreEl.style.color = barColor;
        scoreEl.textContent = `${score}/${maxScore}`;
        row.appendChild(scoreEl);

        criteriaWrap.appendChild(row);
      });

      section.appendChild(criteriaWrap);
    }

    // Feedback text
    if (grading.feedback) {
      const feedback = document.createElement("div");
      feedback.style.cssText = "margin-top: 16px; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap;";
      feedback.textContent = grading.feedback;
      section.appendChild(feedback);
    }

    return section;
  }

  // -----------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, " ");
  }

  function formatGoal(goal) {
    const map = {
      strength: "Strength",
      hypertrophy: "Hypertrophy",
      speed: "Speed",
      power: "Power",
      conditioning: "Conditioning",
      general_fitness: "General Fitness",
      athleticism: "Athleticism"
    };
    return map[goal] || capitalize(goal || "Training");
  }

  function formatMode(mode) {
    const map = {
      gym_only: "Gym Only",
      rehab_only: "Rehab Focus",
      both: "Gym + Rehab Integrated"
    };
    return map[mode] || capitalize(mode || "");
  }

  function formatEquipment(eq) {
    const map = {
      full_gym: "Full Gym",
      basic_gym: "Basic Gym",
      home_db_bands: "Home (DB + Bands)",
      minimal: "Minimal"
    };
    return map[eq] || capitalize(eq || "N/A");
  }

  function formatBlockType(type) {
    const map = {
      rehab_warmup: "Rehab Warmup",
      general_warmup: "General Warmup",
      main_gym: "Main Training",
      rehab_accessories: "Rehab Accessories",
      conditioning: "Conditioning",
      core: "Core Work",
      rehab_mobility: "Mobility & ROM",
      rehab_activation: "Activation & Isometrics",
      rehab_strengthening: "Progressive Strengthening",
      rehab_proprioception: "Balance & Proprioception",
      rehab_cooldown: "Cool-down"
    };
    return map[type] || capitalize((type || "").replace(/_/g, " "));
  }

  function formatCriterionLabel(key) {
    return key
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  // -----------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------

  return {
    init,
    updateGrading,
    updateValidation,
    render
  };
})();
