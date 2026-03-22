/* ===================================================================
   TOASTED — Main App Controller
   Orchestrates onboarding, API calls, loading states, and plan display.
   =================================================================== */

const App = (() => {
  "use strict";

  const API_BASE = "/api";
  let appEl = null;
  let currentPlan = null;
  let currentProfile = null;

  // Loading step messages
  const LOADING_STEPS = [
    "Building your profile...",
    "Retrieving relevant research...",
    "Generating your personalised plan...",
    "Validating exercise safety...",
    "Finalising programme structure..."
  ];

  // -----------------------------------------------------------------
  // Init — called on page load
  // -----------------------------------------------------------------

  function init() {
    appEl = document.getElementById("app");
    if (!appEl) {
      console.error("Toasted: #app element not found");
      return;
    }
    startOnboarding();
  }

  // -----------------------------------------------------------------
  // Start / restart onboarding
  // -----------------------------------------------------------------

  function startOnboarding() {
    currentPlan = null;
    currentProfile = null;
    appEl.innerHTML = "";

    Onboarding.init(appEl, {
      onComplete: handleOnboardingComplete,
      onRedFlag: handleRedFlag
    });
  }

  // -----------------------------------------------------------------
  // Onboarding complete -> generate plan
  // -----------------------------------------------------------------

  async function handleOnboardingComplete(profile) {
    currentProfile = profile;
    showLoading();

    try {
      const result = await generatePlan(profile);
      currentPlan = result.plan;
      showPlan(result.plan, result.validation, result.grade);
    } catch (err) {
      showError(
        "Plan Generation Failed",
        err.message || "Something went wrong. Please try again.",
        true
      );
    }
  }

  // -----------------------------------------------------------------
  // Red flag handler
  // -----------------------------------------------------------------

  function handleRedFlag(profile, redFlagInfo) {
    currentProfile = profile;
    // Profile is saved in memory; user can restart later
    console.log("Profile saved (red flag):", profile);
    console.log("Red flag info:", redFlagInfo);
    // The red flag screen is already displayed by the onboarding module
  }

  // -----------------------------------------------------------------
  // API: Generate plan
  // -----------------------------------------------------------------

  async function generatePlan(profile) {
    const response = await fetch(`${API_BASE}/generate-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile)
    });

    if (!response.ok) {
      let errorMsg = `Server error (${response.status})`;
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorData.message || errorMsg;
      } catch (_) {
        // Response wasn't JSON
      }
      throw new Error(errorMsg);
    }

    const data = await response.json();
    return data;
  }

  // -----------------------------------------------------------------
  // API: Grade plan
  // -----------------------------------------------------------------

  async function gradePlan(plan) {
    const payload = {
      plan: plan,
      user_profile: currentProfile
    };

    const response = await fetch(`${API_BASE}/grade-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      let errorMsg = `Grading failed (${response.status})`;
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorData.message || errorMsg;
      } catch (_) {
        // Response wasn't JSON
      }
      throw new Error(errorMsg);
    }

    const data = await response.json();
    return data;
  }

  // -----------------------------------------------------------------
  // Loading screen with animated steps
  // -----------------------------------------------------------------

  function showLoading() {
    appEl.innerHTML = "";
    const screen = document.createElement("div");
    screen.className = "loading-screen";

    const spinner = document.createElement("div");
    spinner.className = "spinner";
    screen.appendChild(spinner);

    const text = document.createElement("div");
    text.className = "loading-text";
    text.textContent = "Generating your plan...";
    screen.appendChild(text);

    const stepsContainer = document.createElement("div");
    stepsContainer.className = "loading-steps";

    LOADING_STEPS.forEach((stepText, i) => {
      const step = document.createElement("div");
      step.className = "loading-step" + (i === 0 ? " active" : "");
      step.setAttribute("data-step-index", i);
      step.innerHTML = `<div class="step-indicator"></div><span>${stepText}</span>`;
      stepsContainer.appendChild(step);
    });

    screen.appendChild(stepsContainer);
    appEl.appendChild(screen);

    // Animate through steps
    let currentStep = 0;
    const stepInterval = setInterval(() => {
      currentStep++;
      if (currentStep >= LOADING_STEPS.length) {
        clearInterval(stepInterval);
        return;
      }

      // Mark previous as done
      const prevEl = stepsContainer.querySelector(`[data-step-index="${currentStep - 1}"]`);
      if (prevEl) {
        prevEl.classList.remove("active");
        prevEl.classList.add("done");
      }

      // Mark current as active
      const currEl = stepsContainer.querySelector(`[data-step-index="${currentStep}"]`);
      if (currEl) {
        currEl.classList.add("active");
      }

      // Update main text
      text.textContent = LOADING_STEPS[currentStep];
    }, 2000);

    // Store interval ref so we can clean up
    screen._stepInterval = stepInterval;
  }

  // -----------------------------------------------------------------
  // Show plan
  // -----------------------------------------------------------------

  function showPlan(plan, validation, grading) {
    appEl.innerHTML = "";

    PlanDisplay.init(appEl, plan, {
      validation: validation || plan._validation || null,
      grading: grading || plan._grading || null,
      onNewPlan: startOnboarding,
      onGradePlan: handleGradePlan
    });
  }

  // -----------------------------------------------------------------
  // Grade plan handler
  // -----------------------------------------------------------------

  async function handleGradePlan(plan) {
    // Show a mini loading overlay
    const overlay = document.createElement("div");
    overlay.style.cssText = `
      position: fixed;
      inset: 0;
      background: rgba(10, 10, 10, 0.85);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    `;
    overlay.innerHTML = `
      <div class="spinner"></div>
      <div class="loading-text" style="margin-top: 16px;">Grading your plan...</div>
    `;
    document.body.appendChild(overlay);

    try {
      const gradingResult = await gradePlan(plan);
      document.body.removeChild(overlay);
      PlanDisplay.updateGrading(gradingResult);
    } catch (err) {
      document.body.removeChild(overlay);
      // Show inline error
      const errorAlert = document.createElement("div");
      errorAlert.className = "alert-block urgent";
      errorAlert.style.cssText = "position: fixed; bottom: 20px; left: 20px; right: 20px; z-index: 1000; max-width: 500px; margin: 0 auto;";
      errorAlert.innerHTML = `
        <div class="alert-title">Grading Failed</div>
        <div class="alert-body">${escapeHtml(err.message || "Could not grade the plan. Please try again.")}</div>
      `;
      document.body.appendChild(errorAlert);
      setTimeout(() => {
        if (errorAlert.parentNode) {
          errorAlert.parentNode.removeChild(errorAlert);
        }
      }, 5000);
    }
  }

  // -----------------------------------------------------------------
  // Error screen
  // -----------------------------------------------------------------

  function showError(title, message, showRetry = false) {
    appEl.innerHTML = "";
    const screen = document.createElement("div");
    screen.className = "error-screen";

    screen.innerHTML = `
      <div class="error-icon">\u274C</div>
      <div class="error-title">${escapeHtml(title)}</div>
      <div class="error-message">${escapeHtml(message)}</div>
    `;

    const actionRow = document.createElement("div");
    actionRow.className = "action-row center";

    if (showRetry && currentProfile) {
      const retryBtn = document.createElement("button");
      retryBtn.className = "btn btn-primary";
      retryBtn.textContent = "Try Again";
      retryBtn.addEventListener("click", () => {
        handleOnboardingComplete(currentProfile);
      });
      actionRow.appendChild(retryBtn);
    }

    const restartBtn = document.createElement("button");
    restartBtn.className = "btn btn-secondary";
    restartBtn.textContent = "Start Over";
    restartBtn.addEventListener("click", startOnboarding);
    actionRow.appendChild(restartBtn);

    screen.appendChild(actionRow);
    appEl.appendChild(screen);
  }

  // -----------------------------------------------------------------
  // Utility
  // -----------------------------------------------------------------

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // -----------------------------------------------------------------
  // Auto-init on DOMContentLoaded
  // -----------------------------------------------------------------

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // -----------------------------------------------------------------
  // Public API (mostly for debugging)
  // -----------------------------------------------------------------

  return {
    init,
    startOnboarding,
    getCurrentPlan: () => currentPlan,
    getCurrentProfile: () => currentProfile
  };
})();
