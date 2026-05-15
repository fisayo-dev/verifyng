"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import ResultDetailsPanel from "@/components/results/result-details-panel";
import {
  getStoredVerificationSession,
  getVerificationResult,
} from "@/lib/verification";
import { isTerminalVerificationStatus } from "@/types/verification";
import type { VerificationResult } from "@/types/verification";

const POLL_INTERVAL_MS = 3000;

interface ResultDetailsClientProps {
  jobId: string;
}

const ResultDetailsClient = ({ jobId }: ResultDetailsClientProps) => {
  const searchParams = useSearchParams();
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [pollUrl, setPollUrl] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<string | null>(null);

  useEffect(() => {
    const directPollUrl = searchParams.get("poll_url");

    if (directPollUrl) {
      queueMicrotask(() => {
        setPollUrl(directPollUrl);
        setSessionStatus(searchParams.get("status"));
      });
      return;
    }

    queueMicrotask(() => {
      const session = getStoredVerificationSession(jobId);

      if (!session) {
        setIsPolling(false);
        setPollError(
          "No saved verification session was found for this job. Start from the upload page so the app can recover the poll URL.",
        );
        return;
      }

      setPollUrl(session.poll_url);
      setSessionStatus(session.status);
    });
  }, [jobId, searchParams]);

  useEffect(() => {
    if (!pollUrl) {
      return;
    }

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const poll = async () => {
      try {
        const nextResult = await getVerificationResult(pollUrl);

        if (cancelled) {
          return;
        }

        setResult(nextResult);
        setPollError(null);
        setSessionStatus(nextResult.status);

        if (isTerminalVerificationStatus(nextResult.status)) {
          setIsPolling(false);
          return;
        }

        timeoutId = setTimeout(() => {
          void poll();
        }, POLL_INTERVAL_MS);
      } catch (error) {
        if (cancelled) {
          return;
        }

        setIsPolling(false);
        setPollError(
          "Unable to reach the poll endpoint. Please try again in a few moments.",
        );
        console.error(error);
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [pollUrl]);

  const beginPolling = () => {
    setResult(null);
    setPollError(null);

    const session = getStoredVerificationSession(jobId);

    if (session?.poll_url) {
      setPollUrl(session.poll_url);
      setSessionStatus(session.status);
      setIsPolling(true);
      return;
    }

    setIsPolling(false);
    setPollError(
      "No saved verification session was found for this job. Start from the upload page so the app can recover the poll URL.",
    );
  };

  return (
    <ResultDetailsPanel
      jobId={jobId}
      result={result}
      isPolling={isPolling}
      pollError={pollError}
      onRetry={beginPolling}
      sessionStatus={sessionStatus}
    />
  );
};

export default ResultDetailsClient;
