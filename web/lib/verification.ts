import { VERIFICATION_SESSION_PREFIX } from "@/constants/verification";
import api from "@/lib/axios";
import type {
  StoredVerificationSession,
  VerificationCheckoutResponse,
  VerificationResult,
  VerificationStatus,
} from "@/types/verification";
import {
  isTerminalVerificationStatus,
  normalizeVerificationStatus,
} from "@/types/verification";

const resolvePollUrl = (pollUrl: string) => pollUrl.trim();

const readStoredVerificationSession = (
  rawValue: string | null,
): StoredVerificationSession | null => {
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as StoredVerificationSession;
  } catch {
    return null;
  }
};

export const getStoredVerificationSession = (jobId: string) => {
  if (typeof window === "undefined") {
    return null;
  }

  return readStoredVerificationSession(
    window.localStorage.getItem(`${VERIFICATION_SESSION_PREFIX}${jobId}`),
  );
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

export const updateVerificationSession = (
  jobId: string,
  patch: Partial<StoredVerificationSession>,
) => {
  if (typeof window === "undefined") {
    return null;
  }

  const existingSession = getStoredVerificationSession(jobId);

  if (!existingSession) {
    return null;
  }

  const nextSession: StoredVerificationSession = {
    ...existingSession,
    ...patch,
    saved_at: new Date().toISOString(),
  };

  window.localStorage.setItem(
    `${VERIFICATION_SESSION_PREFIX}${jobId}`,
    JSON.stringify(nextSession),
  );

  return nextSession;
};

export const getLatestStoredVerificationSession = (onlyTerminal = false) => {
  if (typeof window === "undefined") {
    return null;
  }

  let latestSession: StoredVerificationSession | null = null;

  for (let index = 0; index < window.localStorage.length; index += 1) {
    const key = window.localStorage.key(index);

    if (!key || !key.startsWith(VERIFICATION_SESSION_PREFIX)) {
      continue;
    }

    const session = readStoredVerificationSession(
      window.localStorage.getItem(key),
    );

    if (!session) {
      continue;
    }

    if (onlyTerminal && !isTerminalVerificationStatus(session.status)) {
      continue;
    }

    if (
      !latestSession ||
      new Date(session.saved_at).getTime() >
        new Date(latestSession.saved_at).getTime()
    ) {
      latestSession = session;
    }
  }

  return latestSession;
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

  const response = await api.post<VerificationCheckoutResponse>(
    "/verify",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return {
    ...response.data,
    status: normalizeVerificationStatus(response.data.status),
  };
};

export const getVerificationResult = async (
  pollUrl: string,
): Promise<VerificationResult> => {
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
