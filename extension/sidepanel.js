const runBtn = document.getElementById("runBtn");
const taskEl = document.getElementById("task");
const apiUrlEl = document.getElementById("apiUrl");
const statusEl = document.getElementById("status");
const taskOutEl = document.getElementById("taskOut");
const stepsOutEl = document.getElementById("stepsOut");
const logsOutEl = document.getElementById("logsOut");

function renderSteps(steps = []) {
  stepsOutEl.innerHTML = "";
  if (!steps.length) {
    stepsOutEl.textContent = "No steps.";
    return;
  }

  steps.forEach((step) => {
    const div = document.createElement("div");
    div.className = "step";

    const screen = step.screenshot
      ? `<div>Screenshot: <a href="${step.screenshot}" target="_blank">${step.screenshot}</a></div>`
      : "";

    div.innerHTML = `
      <div><strong>#${step.step}</strong> ${step.action} (${step.success ? "ok" : "fail"})</div>
      <div>URL: ${step.url || "-"}</div>
      <div>Data: <code>${JSON.stringify(step.data || {})}</code></div>
      ${step.error ? `<div>Error: ${step.error}</div>` : ""}
      ${screen}
    `;
    stepsOutEl.appendChild(div);
  });
}

runBtn.addEventListener("click", async () => {
  const task = taskEl.value.trim();
  if (!task) {
    statusEl.textContent = "Please enter a task.";
    return;
  }

  statusEl.textContent = "Running...";
  taskOutEl.textContent = task;
  logsOutEl.textContent = "";
  stepsOutEl.innerHTML = "";

  chrome.runtime.sendMessage(
    {
      type: "RUN_TASK",
      task,
      apiUrl: apiUrlEl.value.trim()
    },
    (response) => {
      if (chrome.runtime.lastError) {
        statusEl.textContent = "Error: " + chrome.runtime.lastError.message;
        return;
      }

      if (!response?.ok) {
        statusEl.textContent = "Backend request failed.";
        logsOutEl.textContent = response?.error || "Unknown error";
        return;
      }

      const result = response.data;
      statusEl.textContent = result.blocked ? "Task blocked by safety policy." : "Completed.";
      renderSteps(result.steps || []);

      const debug = result.debug || {};
      logsOutEl.textContent = JSON.stringify(
        {
          matched_skill: debug.matched_skill,
          planner_reasoning_summary: debug.planner_reasoning_summary,
          past_experience_used: debug.past_experience_used,
          step_traces: debug.step_traces || []
        },
        null,
        2
      );
    }
  );
});
