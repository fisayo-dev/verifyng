import api from "@/lib/axios";
import type { VerificationResult } from "@/types/verification";

export const getVerificationResult = async (
  jobId: string,
): Promise<VerificationResult> => {
  const response = await api.get<VerificationResult>(
    `/result/${encodeURIComponent(jobId)}`,
  );

  return response.data;
};
