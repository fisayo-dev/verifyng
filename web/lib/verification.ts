import api from "@/lib/axios";
import type { VerificationResult } from "@/types/verification";
import { redirect } from "next/navigation";

export const getVerificationResult = async (
  jobId: string,
): Promise<VerificationResult> => {
  const response = await api.get<VerificationResult>(
    `/result/${encodeURIComponent(jobId)}`,
  );

  return response.data;
};

export const verifyDocument = async (file_data: File) => {
  try {
    const formData = new FormData();
    formData.append("file", file_data);

    const response = await api.post("/verify", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    const { checkout_url } = response.data;

    redirect(checkout_url);
  } catch {
    console.error("Verfification failed");
  }
};
