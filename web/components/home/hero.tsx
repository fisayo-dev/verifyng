import Link from "next/link";
import Button from "../general/button";

const Hero = () => {
  return (
    <div className="grid h-100 place-items-center mt-28">
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
        <Link href="/verify">
          <Button>Start Verification</Button>
        </Link>
      </div>
    </div>
  );
};

export default Hero;
