export type VerificationTerminalStatus = "COMPLETE" | "FAILED";
export type VerificationInProgressStatus =
  | "PENDING_PAYMENT"
  | "PAID"
  | "PROCESSING";

export type VerificationStatus =
  | VerificationTerminalStatus
  | VerificationInProgressStatus
  | string;

export interface VerificationCompleteResult {
  id: string;
  status: "COMPLETE";
  trust_score: number;
  verdict: string;
  flags: string[];
  confidence: string;
  layers_run: string[];
}

export interface VerificationFailedResult {
  status: "FAILED";
  flags: string[];
}

export interface VerificationPendingResult {
  id?: string;
  status: VerificationStatus;
  trust_score?: number;
  verdict?: string;
  flags?: string[];
  confidence?: string;
  layers_run?: string[];
}

export interface VerificationCheckoutResponse {
  job_id: string;
  checkout_url: string;
  poll_url: string;
  status: VerificationStatus;
}

export interface StoredVerificationSession extends VerificationCheckoutResponse {
  saved_at: string;
}

export type VerificationResult =
  | VerificationCompleteResult
  | VerificationFailedResult
  | VerificationPendingResult;

export const isVerificationComplete = (
  result: VerificationResult | null,
): result is VerificationCompleteResult => result?.status === "COMPLETE";

export const isVerificationFailed = (
  result: VerificationResult | null,
): result is VerificationFailedResult => result?.status === "FAILED";

export const normalizeVerificationStatus = (value: string): VerificationStatus => {
  const normalized = value.trim().toUpperCase();

  if (
    normalized === "COMPLETE" ||
    normalized === "FAILED" ||
    normalized === "PAID" ||
    normalized === "PROCESSING" ||
    normalized === "PENDING_PAYMENT"
  ) {
    return normalized;
  }

  if (normalized === "PENDING" || normalized === "QUEUED") {
    return "PENDING_PAYMENT";
  }

  if (normalized === "IN_PROGRESS" || normalized === "RUNNING") {
    return "PROCESSING";
  }

  return normalized;
};

export const isTerminalVerificationStatus = (status: VerificationStatus) =>
  status === "COMPLETE" || status === "FAILED";
