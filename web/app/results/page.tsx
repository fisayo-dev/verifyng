"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getLatestStoredVerificationSession } from "@/lib/verification";
import { CircleIcon } from "lucide-react";

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
      <div className="grid gap-6">
        <h1 className="text-4xl font-extrabold">Fetching results</h1>
        <span className="mx-auto max-w-xl  text-foreground/75">
          <CircleIcon className="text-8xl inline-block animate-spin" />
        </span>
      </div>
    </div>
  );
};

export default ResultsIndexPage;
