"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRightIcon, DocumentIcon } from "@heroicons/react/24/outline";
import {
  storeVerificationSession,
  submitVerificationDocument,
} from "@/lib/verification";
import VerifyUploadDropzone from "@/components/verify/verify-upload-dropzone";

const demoJobId = process.env.NEXT_PUBLIC_TEST_JOB_ID?.trim() ?? "";

const VerifyWorkspace = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!selectedFile || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await submitVerificationDocument(selectedFile);
      storeVerificationSession(response);
      window.location.assign(response.checkout_url);
    } catch (error) {
      console.error(error);
      setSubmitError(
        "Unable to start verification. Please try again with the same file.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-container grid gap-8 pb-20">
      <div className="grid gap-3 text-center">
        <h2 className="text-4xl font-extrabold">Upload Certificate</h2>
        <p className="inline-flex mx-auto w-fit items-center gap-2 rounded-full border border-primary/15 bg-white px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/5">
          <DocumentIcon className="h-5 w-5" />
          <span>Image/PDF</span>
        </p>
      </div>

      <div className="grid gap-6 ">
        <section className="grid gap-5 rounded-4xl border border-foreground/8 bg-white p-6 shadow-[0_20px_60px_-48px_rgba(23,23,23,0.35)]">
          <VerifyUploadDropzone onFileSelect={setSelectedFile} />

          <div className="grid gap-3">
            <button
              type="button"
              onClick={handleUpload}
              disabled={!selectedFile || isSubmitting}
              className="mx-auto inline-flex w-fit items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-primary/40"
            >
              <span>{isSubmitting ? "Starting checkout..." : "Continue to checkout"}</span>
              <ArrowRightIcon className="h-4 w-4" />
            </button>

            {submitError && (
              <p className="text-center text-sm text-danger">{submitError}</p>
            )}
          </div>

        </section>
      </div>
    </div>
  );
};

export default VerifyWorkspace;
