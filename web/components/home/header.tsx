 "use client";

import { useState } from "react";
import {
  Bars3Icon,
  ShieldCheckIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import Button from "../general/button";
import Link from "next/link";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/#features", label: "Features" },
  { href: "/verify", label: "Verify" },
  { href: "/results/demo", label: "Demo Verification" },
];

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="fixed z-30 w-full py-4 backdrop-blur-sm bg-transparent">
      <div className="app-container relative">
        <div className="flex items-center justify-between rounded-full border border-foreground/8 bg-white/90 px-4 py-3 shadow-[0_18px_40px_-28px_rgba(23,23,23,0.2)]">
          <Link
            href="/"
            className="text-2xl font-bold flex items-center gap-2"
            onClick={() => setIsMenuOpen(false)}
          >
          <ShieldCheckIcon className="w-6 h-6 text-primary" />
          <span>VerifyNG</span>
          </Link>

          <div className="hidden md:flex items-center justify-center gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-full px-3 py-2 text-sm transition-colors hover:bg-primary/5"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="hidden md:block">
            <Button>Signup</Button>
          </div>

          <button
            type="button"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-foreground/10 text-foreground transition-colors hover:bg-primary/5 md:hidden"
            onClick={() => setIsMenuOpen((open) => !open)}
            aria-expanded={isMenuOpen}
            aria-label={isMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            {isMenuOpen ? (
              <XMarkIcon className="h-5 w-5" />
            ) : (
              <Bars3Icon className="h-5 w-5" />
            )}
          </button>
        </div>

        {isMenuOpen ? (
          <div className="mt-3 grid gap-2 rounded-3xl border border-foreground/8 bg-white/95 p-3 shadow-[0_20px_50px_-32px_rgba(23,23,23,0.24)] md:hidden">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-2xl px-4 py-3 text-sm transition-colors hover:bg-primary/5"
                onClick={() => setIsMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <Button className="mt-1 w-full">Signup</Button>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default Header;
