import { ShieldCheckIcon } from "@heroicons/react/24/outline";
import Button from "../general/button";
import Link from "next/link";

const Header = () => {
  return (
    <div className="fixed w-full py-6 backdrop-blur-2xl">
      <div className="app-container flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold flex items-center gap-2">
          <ShieldCheckIcon className="w-6 h-6 text-primary" />
          <span>VerifyNG</span>
        </Link>
        <div className="hidden md:flex items-center space-x-6 justify-center">
          <p>Features</p>
          <p>How to use</p>
        </div>

        <Button>Signup</Button>
      </div>
    </div>
  );
};

export default Header;
