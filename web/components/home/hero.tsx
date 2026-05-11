import Link from "next/link";

const Hero = () => {
  return (
    <section className="relative isolate overflow-hidden pb-10">
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 opacity-70"
        style={{
          backgroundImage: `
            radial-gradient(circle at top, rgba(0, 102, 204, 0.18), transparent 42%),
            linear-gradient(rgba(0, 102, 204, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 102, 204, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: "100% 100%, 42px 42px, 42px 42px",
          backgroundPosition: "center, center, center",
          maskImage:
            "linear-gradient(to bottom, transparent, black 18%, black 82%, transparent)",
          WebkitMaskImage:
            "linear-gradient(to bottom, transparent, black 18%, black 82%, transparent)",
        }}
      />
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-0 -z-10 h-40 bg-linear-to-b from-background via-background/80 to-transparent"
      />
      <div className="grid h-full place-items-center">
        <div className="app-container flex flex-col place-items-center gap-6 text-center">
          <div className="w-auto rounded-full border border-primary bg-primary/10 px-4 py-1 text-sm text-primary">
            Built for employees
          </div>
          <div className="grid gap-3">
            <h2 className="text-5xl font-bold md:max-w-4xl lg:text-6xl">
              Verify academic certificates with the power of AI.
            </h2>
            <p>
              Nigeria&apos;s first AI-powered academic certificate verification
              platform.
            </p>
          </div>
          <Link
            href="/verify"
            className="rounded-full bg-primary px-5 py-3 text-white transition-all hover:scale-110 hover:cursor-pointer hover:bg-primary/80"
          >
            Start Verification
          </Link>
        </div>
      </div>
    </section>
  );
};

export default Hero;
