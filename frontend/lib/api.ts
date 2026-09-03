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

export type SupportChatResponse = {
  request_id: string;
  answer: string;
  decision: string;
  blocked: boolean;
  guardrails: Array<{
    guardrail: string;
    decision: string;
    risk: string;
    confidence: number;
    reason: string;
  }>;
  context_documents: Array<{
    document_id: string;
    action: string;
    risk: string;
    source: string;
    reason: string;
    content: string;
  }>;
  allowed_context: Array<{ content: string }>;
  tool_calls: Array<{
    tool_name: string;
    decision: string;
    risk: string;
    reason: string;
    executed: boolean;
    result: Record<string, string>;
  }>;
  trace: Array<{
    component: string;
    decision: string;
    reason: string;
  }>;
  tokens: {
    input: number;
    output: number;
  };
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

export async function sendSupportMessage(message: string): Promise<SupportChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/support/chat`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": API_KEY,
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`Support agent request failed with ${response.status}`);
  }

  return response.json();
}
