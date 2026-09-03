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

export type AttackSeed = {
  seed_id: string;
  category: string;
  severity: string;
  payload: string;
  expected_behavior: string;
  metadata: Record<string, string>;
};

export type Finding = {
  finding_id: string;
  severity: string;
  title: string;
  attack_id: string;
  category: string;
  affected_component: string;
  description: string;
  impact: string;
  root_cause: string;
  recommendation: string;
  status: string;
};

export type CampaignRunResponse = {
  campaign: {
    campaign_id: string;
    tenant_id: string;
    application_id: string | null;
    name: string;
    status: string;
    attack_count: number;
    mutation_depth: number;
    started_at: string;
    completed_at: string | null;
  };
  score: {
    overall: number;
    prompt_security: number;
    rag_security: number;
    agent_security: number;
    data_security: number;
    availability: number;
    attack_success_rate: number;
    detection_rate: number;
    false_positive_rate: number;
    false_negative_rate: number;
    attacks_executed: number;
    successful_attacks: number;
  };
  results: Array<{
    variant: {
      attack_id: string;
      seed_id: string;
      category: string;
      severity: string;
      payload: string;
      expected_behavior: string;
      parent_attack_id: string | null;
      mutation_strategy: string;
      metadata: Record<string, string>;
    };
    evaluation: {
      attack_id: string;
      category: string;
      severity: string;
      blocked: boolean;
      allowed: boolean;
      successful_attack: boolean;
      false_positive: boolean;
      false_negative: boolean;
      detection_signals: string[];
      latency_ms: number;
      tokens: Record<string, number>;
      finding: Finding | null;
    };
    trace: Array<{ component: string; decision: string; reason: string }>;
  }>;
  findings: Finding[];
};

export type ObservabilitySummary = {
  request_count: number;
  security_events: number;
  attack_results: number;
  campaigns: number;
  findings: number;
  guardrail_blocks: number;
  pii_redactions: number;
  latest_score: number;
};

export type TraceRecord = {
  id: string;
  request_id: string;
  application_id: string | null;
  spans: Array<{
    component: string;
    decision: string;
    reason: string;
  }>;
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

export async function runCampaign(): Promise<CampaignRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/red-team/campaigns`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": API_KEY,
    },
    body: JSON.stringify({
      name: "Deterministic Demo Campaign",
      attack_count: 5,
      mutation_depth: 2,
    }),
  });

  if (!response.ok) {
    throw new Error(`Campaign request failed with ${response.status}`);
  }

  return response.json();
}

export async function getLatestCampaign(): Promise<CampaignRunResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/red-team/campaigns/latest`, {
      cache: "no-store",
      headers: { "x-api-key": API_KEY },
    });
    if (!response.ok) {
      return null;
    }
    return response.json();
  } catch {
    return null;
  }
}

export async function getAttackCatalog(): Promise<AttackSeed[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/red-team/attacks`, {
      cache: "no-store",
      headers: { "x-api-key": API_KEY },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch {
    return [];
  }
}

export async function getFindings(): Promise<Finding[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/red-team/findings`, {
      cache: "no-store",
      headers: { "x-api-key": API_KEY },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch {
    return [];
  }
}

export async function getObservabilitySummary(): Promise<ObservabilitySummary> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/observability/summary`, {
      cache: "no-store",
      headers: { "x-api-key": API_KEY },
    });
    if (!response.ok) {
      throw new Error("summary unavailable");
    }
    return response.json();
  } catch {
    return {
      request_count: 0,
      security_events: 0,
      attack_results: 0,
      campaigns: 0,
      findings: 0,
      guardrail_blocks: 0,
      pii_redactions: 0,
      latest_score: 0,
    };
  }
}

export async function getTraces(): Promise<TraceRecord[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/observability/traces`, {
      cache: "no-store",
      headers: { "x-api-key": API_KEY },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch {
    return [];
  }
}
