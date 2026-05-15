import api from "@/lib/axios";
import type {
  StoredVerificationSession,
  VerificationCheckoutResponse,
  VerificationResult,
  VerificationStatus,
} from "@/types/verification";
import { normalizeVerificationStatus } from "@/types/verification";
import axios from "axios";

const VERIFICATION_SESSION_PREFIX = "verifyng:verification:";

const resolvePollUrl = (pollUrl: string) => pollUrl.trim();

export const getStoredVerificationSession = (jobId: string) => {
  if (typeof window === "undefined") {
    return null;
  }

  const rawValue = window.localStorage.getItem(
    `${VERIFICATION_SESSION_PREFIX}${jobId}`,
  );

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as StoredVerificationSession;
  } catch {
    return null;
  }
};

export const storeVerificationSession = (
  session: VerificationCheckoutResponse,
) => {
  if (typeof window === "undefined") {
    return;
  }

  const payload: StoredVerificationSession = {
    ...session,
    status: normalizeVerificationStatus(session.status),
    saved_at: new Date().toISOString(),
  };

  window.localStorage.setItem(
    `${VERIFICATION_SESSION_PREFIX}${session.job_id}`,
    JSON.stringify(payload),
  );
};

export const clearVerificationSession = (jobId: string) => {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(`${VERIFICATION_SESSION_PREFIX}${jobId}`);
};

export const submitVerificationDocument = async (
  file: File,
): Promise<VerificationCheckoutResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<VerificationCheckoutResponse>("/verify", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return {
    ...response.data,
    status: normalizeVerificationStatus(response.data.status),
  };
};

export const getVerificationResult = async (
  pollUrl: string,
  jobId: string,
): Promise<VerificationResult> => {
  console.log("POLL URL", pollUrl)
  const response = await api.get<VerificationResult>(resolvePollUrl(pollUrl));
  const result = response.data;

  return {
    ...result,
    status: normalizeVerificationStatus(result.status),
  };
};

export const getVerificationSessionStatus = (
  session: StoredVerificationSession | null,
): VerificationStatus | null => session?.status ?? null;
