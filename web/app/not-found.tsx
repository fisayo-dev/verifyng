import Link from "next/link";

export default function NotFound() {
  return (
    <main className="relative flex min-h-[calc(100vh-5rem)] items-center overflow-hidden px-5 py-16">
      <div className="absolute inset-0 " />

      <section className="app-container relative">
        <div className="mx-auto max-w-3xl rounded-4xl border border-primary/10 bg-white/80 p-8 text-center shadow-[0_24px_80px_rgba(0,0,0,0.08)] backdrop-blur md:p-12">
          <p className="text-sm font-semibold uppercase tracking-[0.4em] text-primary">
            404 Error
          </p>
          <h1 className="mt-6 text-4xl font-black tracking-tight text-foreground md:text-6xl">
            This page could not be verified.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-gray md:text-lg">
            The link may be outdated, moved, or typed incorrectly. Head back to
            VerifyNG and continue from a valid route.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/"
              className="rounded-full bg-primary px-6 py-3 font-semibold text-white transition hover:scale-105 hover:bg-primary/90"
            >
              Return Home
            </Link>
            <Link
              href="/#features"
              className="rounded-full border border-primary/15 px-6 py-3 font-semibold text-primary transition hover:border-primary/35 hover:bg-primary/5"
            >
              Explore Features
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
