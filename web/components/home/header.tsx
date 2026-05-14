"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bars3Icon,
  ShieldCheckIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import gsap from "gsap";
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
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const navRef = useRef<HTMLDivElement | null>(null);
  const mobileMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (reduceMotion.matches) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.from(wrapperRef.current, {
        y: -18,
        opacity: 0,
        duration: 0.6,
        ease: "power3.out",
      });

      gsap.from(navRef.current?.children ?? [], {
        y: -10,
        opacity: 0,
        duration: 0.4,
        ease: "power2.out",
        stagger: 0.08,
        delay: 0.15,
      });
    }, wrapperRef);

    return () => {
      ctx.revert();
    };
  }, []);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (reduceMotion.matches) {
      return;
    }

    if (!mobileMenuRef.current) {
      return;
    }

    if (isMenuOpen) {
      gsap.fromTo(
        mobileMenuRef.current,
        { y: -12, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.28, ease: "power2.out" },
      );
      return;
    }

    gsap.set(mobileMenuRef.current, { clearProps: "all" });
  }, [isMenuOpen]);

  return (
    <div className="fixed z-30 w-full bg-transparent py-4 backdrop-blur-sm">
      <div className="app-container relative">
        <div
          ref={wrapperRef}
          className="flex items-center justify-between rounded-full border border-foreground/8 bg-white/90 px-4 py-3 shadow-[0_18px_40px_-28px_rgba(23,23,23,0.2)]"
        >
          <Link
            href="/"
            className="flex items-center gap-2 text-2xl font-bold"
            onClick={() => setIsMenuOpen(false)}
          >
            <ShieldCheckIcon className="h-6 w-6 text-primary" />
            <span>VerifyNG</span>
          </Link>

          <div
            ref={navRef}
            className="hidden items-center justify-center gap-2 md:flex"
          >
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

          <Link
            href="/verify"
            className="hidden md:inline-flex items-center justify-center rounded-full bg-primary px-6 py-3 text-white transition-all hover:scale-105 hover:bg-primary/85 text-sm"
          >
            Start Verification
          </Link>

          <button
            type="button"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-foreground/10 text-foreground transition-colors hover:bg-primary/5 md:hidden"
            onClick={() => setIsMenuOpen((open) => !open)}
            aria-expanded={isMenuOpen}
            aria-label={
              isMenuOpen ? "Close navigation menu" : "Open navigation menu"
            }
          >
            {isMenuOpen ? (
              <XMarkIcon className="h-5 w-5" />
            ) : (
              <Bars3Icon className="h-5 w-5" />
            )}
          </button>
        </div>

        {isMenuOpen ? (
          <div
            ref={mobileMenuRef}
            className="overflow-hidden mt-3 grid gap-2 rounded-3xl border border-foreground/8 bg-white/95 p-3 shadow-[0_20px_50px_-32px_rgba(23,23,23,0.24)] md:hidden"
          >
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
            <Button className="mt-1 w-full text-sm">
              <Link href="/verify">Start Verification</Link>
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default Header;
