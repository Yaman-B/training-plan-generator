const API_BASE = "";

async function request(path, options) {
  const res = await fetch(API_BASE + path, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${options?.method || "GET"} ${path} failed (${res.status}): ${body}`);
  }
  return res.json();
}

function createProfile(profileData) {
  return request("/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profileData),
  });
}

function generatePlan(profileId) {
  return request(`/profile/${profileId}/plan`, { method: "POST" });
}

function generateWeek(weeklyPlanId, targetDate) {
  const query = targetDate ? `?target_date=${targetDate}` : "";
  return request(`/weekly-plan/${weeklyPlanId}/sessions/week${query}`, { method: "POST" });
}

// Read-only fetches, used by the plan-inspection screen.
function getProfile(profileId) {
  return request(`/profile/${profileId}`, { method: "GET" });
}

function getWeeklyPlan(weeklyPlanId) {
  return request(`/weekly-plan/${weeklyPlanId}`, { method: "GET" });
}

function getMonthlyPlan(monthlyPlanId) {
  return request(`/monthly-plan/${monthlyPlanId}`, { method: "GET" });
}

function getYearlyPlan(yearlyPlanId) {
  return request(`/yearly-plan/${yearlyPlanId}`, { method: "GET" });
}
