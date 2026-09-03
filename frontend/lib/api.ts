const API_BASE_URL = process.env.AEGIS_API_BASE_URL || "http://localhost:8000";
const API_KEY = process.env.AEGIS_FRONTEND_API_KEY || "dev-aegis-key";

export type HealthResponse = {
  status: string;
};

export type Application = {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
};

export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return response.json();
  } catch {
    return null;
  }
}

export async function getApplications(): Promise<Application[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/applications`, {
      cache: "no-store",
      headers: {
        "x-api-key": API_KEY,
      },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch {
    return [];
  }
}
