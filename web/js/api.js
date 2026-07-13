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
