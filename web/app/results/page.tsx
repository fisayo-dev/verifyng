"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getLatestStoredVerificationSession } from "@/lib/verification";

const ResultsIndexPage = () => {
  const router = useRouter();

  useEffect(() => {
    const session = getLatestStoredVerificationSession(true);

    if (session) {
      router.replace(`/results/${encodeURIComponent(session.job_id)}`);
    }
  }, [router]);

  return (
    <div className="app-container grid min-h-[50vh] place-items-center pb-20 text-center">
      <div className="grid gap-3">
        <h1 className="text-4xl font-extrabold">Results</h1>
        <p className="mx-auto max-w-xl text-sm text-foreground/75">
          If a verified result exists on this device, you will be redirected to
          it automatically. Otherwise, start a new verification first.
        </p>
      </div>
    </div>
  );
};

export default ResultsIndexPage;
