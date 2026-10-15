const statusIndicator = document.querySelector("#backend-status");
const statusText = statusIndicator.querySelector(".status-text");

async function checkBackend() {
  try {
    const response = await fetch("/api/health", {
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Health check returned ${response.status}`);
    }

    const data = await response.json();
    if (data.status !== "ok") {
      throw new Error("Backend reported an unhealthy status");
    }

    statusIndicator.className = "status status-online";
    statusText.textContent = "Backend connected";
  } catch (error) {
    statusIndicator.className = "status status-offline";
    statusText.textContent = "Backend unavailable";
    console.error("Backend health check failed:", error);
  }
}

checkBackend();
