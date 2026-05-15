"use client";

import Link from "next/link";
import {
  ArrowLeftIcon,
  CheckBadgeIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";
import type { VerificationResult } from "@/types/verification";
import {
  isVerificationComplete,
  isVerificationFailed,
} from "@/types/verification";
import GsapTyping from "@/components/shared/gsap-typing";

interface ResultDetailsPanelProps {
  jobId: string;
  result: VerificationResult | null;
  isPolling: boolean;
  pollError: string | null;
  onRetry: () => void;
  sessionStatus: string | null;
}

const formatLayerName = (value: string) =>
  value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const ANALYSIS_FLAG_PREFIXES = ["AI evidence:", "ML classifier:"] as const;

const splitFlags = (flags: string[]) =>
  flags.reduce(
    (acc, flag) => {
      const isAnalysisDetail = ANALYSIS_FLAG_PREFIXES.some((prefix) =>
        flag.startsWith(prefix),
      );

      if (isAnalysisDetail) {
        acc.analysis.push(flag);
        return acc;
      }

      acc.flags.push(flag);
      return acc;
    },
    { flags: [] as string[], analysis: [] as string[] },
  );

const ResultDetailsPanel = ({
  jobId,
  result,
  isPolling,
  pollError,
  onRetry,
  sessionStatus,
}: ResultDetailsPanelProps) => {
  const isComplete = isVerificationComplete(result);
  const isFailed = isVerificationFailed(result);
  const flags = result?.flags ?? [];
  const { flags: visibleFlags, analysis } = splitFlags(flags);
  const currentStatus =
    result?.status ??
    sessionStatus ??
    (isPolling ? "PROCESSING" : "PENDING_PAYMENT");
  const isTerminalFailed = currentStatus === "FAILED" || isFailed;
  const isTerminalComplete = currentStatus === "COMPLETE" || isComplete;
  const completeResult = isComplete ? result : null;
  const layersRun = completeResult?.layers_run ?? [];
  const hasLayers = layersRun.length > 0;

  return (
    <div className="app-container grid gap-8 pb-20">
      <div className="grid gap-4">
        <Link
          href="/verify"
          className="inline-flex w-fit items-center gap-2 rounded-full border border-primary/15 bg-white px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/5"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          <span>Back to verify</span>
        </Link>
        <div className="grid gap-3 text-center">
          <h1 className="text-4xl font-extrabold">Verification result</h1>
          <p className="mx-auto w-fit rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            Result details
          </p>
        </div>
      </div>

      <section className="grid gap-5 rounded-4xl border border-primary/10 bg-white p-6 shadow-[0_20px_80px_-48px_rgba(0,102,204,0.45)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="grid gap-2">
            <p className="text-sm font-medium text-primary">Job reference</p>
            <h2 className="break-all text-xl font-bold">{jobId}</h2>
          </div>
          <div
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${
              isTerminalComplete ? "bg-success-soft text-success"
              : isTerminalFailed ? "bg-danger-soft text-danger"
              : currentStatus === "PAID" ? "bg-trust-blue-soft text-trust-blue"
              : "bg-primary/10 text-primary"
            }`}
          >
            {isTerminalComplete ?
              <CheckBadgeIcon className="h-5 w-5" />
            : isTerminalFailed ?
              <ExclamationTriangleIcon className="h-5 w-5" />
            : <ClockIcon className="h-5 w-5" />}
            <span>{currentStatus}</span>
          </div>
        </div>

        {pollError ?
          <div className="rounded-2xl border border-danger/20 bg-danger-soft p-4">
            <p className="font-semibold text-danger">Polling failed</p>
            <p className="mt-1 text-sm text-foreground/80">{pollError}</p>
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 inline-flex rounded-full border border-danger/25 px-4 py-2 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white"
            >
              Retry polling
            </button>
          </div>
        : null}

        {isTerminalComplete ?
          <div className="grid gap-5">
            <div className="grid gap-4 rounded-[1.75rem] bg-[linear-gradient(135deg,var(--trust-blue-soft),rgba(255,255,255,0.98))] p-5 md:grid-cols-[1.1fr_0.9fr]">
              <div className="grid gap-4">
                <div className="flex items-center gap-3 text-trust-blue">
                  <ShieldCheckIcon className="h-6 w-6" />
                  <p className="text-lg font-semibold">Trust score</p>
                </div>
                <div className="flex items-end gap-3">
                  <span className="text-6xl font-black leading-none text-trust-blue">
                    {completeResult?.trust_score}
                  </span>
                  <span className="pb-2 text-sm font-medium uppercase tracking-[0.24em] text-trust-blue/70">
                    out of 100
                  </span>
                </div>
                <p className="max-w-xl text-sm text-foreground/75">
                  {completeResult?.verdict} with{" "}
                  {completeResult?.confidence?.toLowerCase()} confidence.
                </p>
              </div>
              <div className="grid gap-3 rounded-3xl bg-white/85 p-5">
                <p className="text-sm font-medium text-gray">
                  Analysis details
                </p>
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-gray">
                    Verdict
                  </p>
                  <p className="mt-1 text-lg font-semibold text-success">
                    {completeResult?.verdict}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-gray">
                    Confidence
                  </p>
                  <p className="mt-1 text-base font-semibold">
                    {completeResult?.confidence}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-3xl border border-foreground/8 bg-background p-5">
                <p className="text-sm font-semibold text-foreground">Flags</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {visibleFlags.length > 0 ?
                    visibleFlags.map((flag) => (
                      <span
                        key={flag}
                        className="rounded-full bg-warning-soft px-3 py-2 text-sm text-foreground"
                      >
                        {flag}
                      </span>
                    ))
                  : <p className="text-sm text-gray">
                      No risk flags were returned.
                    </p>
                  }
                </div>
              </div>
              <div className="rounded-3xl border border-foreground/8 bg-background p-5">
                <p className="text-sm font-semibold text-foreground">
                  Layers run
                </p>
                {hasLayers ?
                  <div className="mt-4 flex flex-wrap gap-2">
                    {layersRun.map((layer) => (
                      <span
                        key={layer}
                        className="rounded-full bg-primary/10 px-3 py-2 text-sm text-primary"
                      >
                        {formatLayerName(layer)}
                      </span>
                    ))}
                  </div>
                : <p className="mt-3 text-sm text-gray">
                    No analysis layers were returned.
                  </p>
                }
              </div>
            </div>

            {analysis.length > 0 ?
              <div className="rounded-3xl border border-trust-blue/10 bg-trust-blue-soft/60 p-5">
                <p className="text-sm font-semibold text-trust-blue">
                  Analysis Details
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {analysis.map((flag) => (
                    <span
                      key={flag}
                      className="rounded-full bg-white px-3 py-2 text-sm text-foreground shadow-sm"
                    >
                      {flag}
                    </span>
                  ))}
                </div>
              </div>
            : null}
          </div>
        : null}

        {isTerminalFailed ?
          <div className="grid gap-4 rounded-[1.75rem] border border-danger/20 bg-danger-soft p-5">
            <p className="text-lg font-semibold text-danger">
              Verification failed
            </p>
            <div className="flex flex-wrap gap-2">
              {visibleFlags.length > 0 ?
                visibleFlags.map((flag) => (
                  <span
                    key={flag}
                    className="rounded-full bg-white px-3 py-2 text-sm text-danger"
                  >
                    {flag}
                  </span>
                ))
              : <p className="text-sm text-foreground/75">
                  The API returned `FAILED` without additional failure flags.
                </p>
              }
            </div>
            {analysis.length > 0 ?
              <div className="rounded-3xl bg-white/70 p-4">
                <p className="text-sm font-semibold text-foreground">
                  Analysis Details
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {analysis.map((flag) => (
                    <span
                      key={flag}
                      className="rounded-full bg-danger-soft px-3 py-2 text-sm text-danger"
                    >
                      {flag}
                    </span>
                  ))}
                </div>
              </div>
            : null}
          </div>
        : null}

        {!isComplete && !isFailed && !pollError ?
          <div className="grid gap-3 rounded-[1.75rem] border border-primary/15 bg-primary/5 p-5">
            <p className="text-lg font-semibold text-foreground">
              {isPolling ? "Polling in progress" : "Ready to poll"}
            </p>
            {isPolling ?
              <GsapTyping />
            : null}
            <p className="text-sm text-foreground/75">
              The page checks the result endpoint every 3 seconds and stops only
              when the API returns `COMPLETE` or `FAILED`.
            </p>
          </div>
        : null}
      </section>
    </div>
  );
};

export default ResultDetailsPanel;
