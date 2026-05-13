"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ResultDetailsPanel from "@/app/results/_components/result-details-panel";
import { getVerificationResult } from "@/lib/verification";
import type { VerificationResult } from "@/types/verification";

const POLL_INTERVAL_MS = 3000;

interface ResultDetailsClientProps {
  jobId: string;
}

const ResultDetailsClient = ({ jobId }: ResultDetailsClientProps) => {
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollJobRef = useRef<(nextJobId: string) => Promise<void>>(async () => {});

  const clearScheduledPoll = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const pollJob = useCallback(async (nextJobId: string): Promise<void> => {
    try {
      const nextResult = await getVerificationResult(nextJobId);

      setResult(nextResult);
      setPollError(null);

      if (
        nextResult.status === "COMPLETE" ||
        nextResult.status === "FAILED"
      ) {
        setIsPolling(false);
        return;
      }

      timeoutRef.current = setTimeout(() => {
        void pollJobRef.current(nextJobId);
      }, POLL_INTERVAL_MS);
    } catch (error) {
      setIsPolling(false);
      setPollError("Unable to reach the result endpoint. Check the job ID and try again.");
      console.error(error);
    }
  }, []);

  useEffect(() => {
    pollJobRef.current = pollJob;
  }, [pollJob]);

  const beginPolling = useCallback(() => {
    clearScheduledPoll();
    setResult(null);
    setPollError(null);
    setIsPolling(true);
    void pollJobRef.current(jobId);
  }, [clearScheduledPoll, jobId]);

  useEffect(() => {
    void pollJobRef.current(jobId);

    return () => {
      clearScheduledPoll();
    };
  }, [clearScheduledPoll, jobId]);

  return (
    <ResultDetailsPanel
      jobId={jobId}
      result={result}
      isPolling={isPolling}
      pollError={pollError}
      onRetry={beginPolling}
    />
  );
};

export default ResultDetailsClient;
