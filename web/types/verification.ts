export type VerificationTerminalStatus = "COMPLETE" | "FAILED";

export type VerificationStatus =
  | VerificationTerminalStatus
  | "PENDING"
  | "PROCESSING"
  | "QUEUED"
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
