"use client";

import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="relative flex min-h-screen items-center overflow-hidden px-5 py-16">
      <div className="absolute inset-0 " />

      <section className="app-container relative">
        <div className="mx-auto max-w-3xl rounded-4xl border border-danger/10 bg-white/85 p-8 text-center shadow-[0_24px_80px_rgba(0,0,0,0.08)] backdrop-blur md:p-12">
          <p className="text-sm font-semibold uppercase tracking-[0.4em] text-danger">
            Application Error
          </p>
          <h1 className="mt-6 text-4xl font-black tracking-tight text-foreground md:text-6xl">
            Something broke while loading this page.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-gray md:text-lg">
            An unexpected error interrupted the request. You can retry this view
            or return to the VerifyNG homepage.
          </p>

          {error.digest ? (
            <p className="mt-4 text-sm text-gray">Reference: {error.digest}</p>
          ) : null}

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <button
              type="button"
              onClick={reset}
              className="rounded-full bg-danger px-6 py-3 font-semibold text-white transition hover:scale-105 hover:bg-danger/90"
            >
              Try Again
            </button>
            <Link
              href="/"
              className="rounded-full border border-primary/15 px-6 py-3 font-semibold text-primary transition hover:border-primary/35 hover:bg-primary/5"
            >
              Return Home
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
