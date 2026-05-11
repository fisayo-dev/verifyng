import Link from "next/link";

const Hero = () => {
  return (
    <div className="grid h-full place-items-center my-28">
      <div className="app-container flex flex-col gap-6 text-center place-items-center">
        <div className="border border-primary py-1 px-3 text-sm rounded-full bg-primary/10 text-primary w-auto">
          Built for employees
        </div>
        <div className="grid gap-3">
          <h2 className="text-5xl lg:text-6xl font-bold md:max-w-4xl ">
            Verify academic certificates with the power of AI.
          </h2>
          <p>
            Nigeria&apos;s first AI-powered academic certificate verification
            platform.
          </p>
        </div>
        <Link
          href="/verify"
          className="bg-primary px-5 py-3 rounded-full text-white hover:bg-primary/80 hover:cursor-pointer hover:scale-110 transition-all"
        >
          Start Verification
        </Link>
      </div>
    </div>
  );
};

export default Hero;
