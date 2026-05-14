import { ShieldCheckIcon } from "@heroicons/react/24/outline";
import Button from "../general/button";
import Link from "next/link";

const Header = () => {
  return (
    <div className="fixed z-30 w-full py-6 backdrop-blur-sm bg-transparent">
      <div className="app-container flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold flex items-center gap-2">
          <ShieldCheckIcon className="w-6 h-6 text-primary" />
          <span>VerifyNG</span>
        </Link>
        <div className="hidden md:flex items-center justify-center space-x-4">
          <Link href="/#features" className="text-center px-3 py-1 rounded-full hover:bg-primary/5">Features</Link>
          <Link href="/results/demo" className="text-center px-3 py-1 rounded-full hover:bg-primary/5">Demo Verfication</Link>
        </div>

        <Button>Signup</Button>
      </div>
    </div>
  );
};

export default Header;
