"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import gsap from "gsap";

const typedMessages = [
  "Checking institution format markers...",
  "Matching award details with extracted metadata...",
  "Flagging the mismatch before report delivery...",
];

const Hero = () => {
  const sectionRef = useRef<HTMLElement | null>(null);
  const badgeRef = useRef<HTMLDivElement | null>(null);
  const headingRef = useRef<HTMLHeadingElement | null>(null);
  const paragraphRef = useRef<HTMLParagraphElement | null>(null);
  const actionsRef = useRef<HTMLDivElement | null>(null);
  const statsRef = useRef<HTMLDivElement | null>(null);
  const visualRef = useRef<HTMLDivElement | null>(null);
  const glowRef = useRef<HTMLDivElement | null>(null);
  const queueCardRef = useRef<HTMLDivElement | null>(null);
  const scoreCardRef = useRef<HTMLDivElement | null>(null);
  const metaGridRef = useRef<HTMLDivElement | null>(null);
  const noteCardRef = useRef<HTMLDivElement | null>(null);
  const progressBarRef = useRef<HTMLDivElement | null>(null);
  const typingTextRef = useRef<HTMLParagraphElement | null>(null);
  const typingCursorRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (reduceMotion.matches) {
      if (typingTextRef.current) {
        typingTextRef.current.textContent = typedMessages[0];
      }
      return;
    }

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.from(badgeRef.current, {
        y: 18,
        opacity: 0,
        duration: 0.45,
      })
        .from(
          headingRef.current,
          {
            y: 30,
            opacity: 0,
            duration: 0.7,
          },
          "-=0.15"
        )
        .from(
          paragraphRef.current,
          {
            y: 22,
            opacity: 0,
            duration: 0.55,
          },
          "-=0.35"
        )
        .from(
          actionsRef.current,
          {
            y: 18,
            opacity: 0,
            duration: 0.45,
          },
          "-=0.28"
        )
        .from(
          statsRef.current?.children ?? [],
          {
            y: 20,
            opacity: 0,
            duration: 0.45,
            stagger: 0.12,
          },
          "-=0.2"
        )
        .from(
          visualRef.current,
          {
            x: 28,
            y: 18,
            opacity: 0,
            rotate: -2,
            duration: 0.8,
          },
          "-=0.7"
        )
        .from(
          [queueCardRef.current, scoreCardRef.current, metaGridRef.current, noteCardRef.current],
          {
            y: 16,
            opacity: 0,
            duration: 0.5,
            stagger: 0.1,
          },
          "-=0.45"
        )
        .from(
          progressBarRef.current,
          {
            scaleX: 0,
            transformOrigin: "left center",
            duration: 0.6,
            ease: "power2.out",
          },
          "-=0.5"
        );

      gsap.to(visualRef.current, {
        y: -10,
        duration: 2.8,
        ease: "sine.inOut",
        repeat: -1,
        yoyo: true,
      });

      gsap.to(glowRef.current, {
        scale: 1.08,
        opacity: 0.9,
        duration: 3.2,
        ease: "sine.inOut",
        repeat: -1,
        yoyo: true,
      });

      gsap.to(typingCursorRef.current, {
        opacity: 0,
        duration: 0.55,
        ease: "power1.inOut",
        repeat: -1,
        yoyo: true,
      });

      const typingState = { length: 0 };
      const typingTimeline = gsap.timeline({ repeat: -1, repeatDelay: 0.35 });

      typedMessages.forEach((message) => {
        typingTimeline
          .set(typingState, {
            length: 0,
            onUpdate: () => {
              if (typingTextRef.current) {
                typingTextRef.current.textContent = "";
              }
            },
          })
          .to(typingState, {
            length: message.length,
            duration: Math.max(1.3, message.length * 0.035),
            ease: "none",
            snap: "length",
            onUpdate: () => {
              if (typingTextRef.current) {
                typingTextRef.current.textContent = message.slice(0, typingState.length);
              }
            },
          })
          .to({}, { duration: 1.1 })
          .to(typingState, {
            length: 0,
            duration: 0.55,
            ease: "none",
            snap: "length",
            onUpdate: () => {
              if (typingTextRef.current) {
                typingTextRef.current.textContent = message.slice(0, typingState.length);
              }
            },
          });
      });
    }, sectionRef);

    return () => {
      ctx.revert();
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative isolate overflow-hidden pb-12 md:pb-20"
    >
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 opacity-80"
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
      <div
        ref={glowRef}
        aria-hidden="true"
        className="absolute left-1/2 top-32 -z-10 h-72 w-72 rounded-full bg-primary/10 blur-3xl"
      />

      <div className="app-container">
        <div className="grid items-center gap-14 lg:grid-cols-[minmax(0,1.05fr)_minmax(22rem,0.95fr)] lg:gap-10">
          <div className="grid gap-7 text-center lg:text-left">
            <div
              ref={badgeRef}
              className="inline-flex w-fit items-center justify-self-center gap-3 rounded-full border border-primary/15 bg-white px-5 py-2 text-xs font-medium text-primary shadow-[0_16px_40px_-28px_rgba(0,102,204,0.4)] lg:justify-self-start"
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
                AI
              </span>
              <span>AI certificate verification for modern hiring teams</span>
            </div>

            <div className="grid gap-5">
              <h1
                ref={headingRef}
                className="max-w-3xl text-4xl font-bold tracking-tight md:text-6xl lg:text-5xl"
              >
                You have the candidate.
                <br />
                We&apos;ll tell you if the
                <br />
                certificate is{" "}
                <span className="text-primary italic">authentic.</span>
              </h1>
              <p
                ref={paragraphRef}
                className="max-w-2xl text-base leading-6 text-gray md:text-lg"
              >
                VerifyNG checks academic certificates in minutes. Upload a
                document, review the extracted details, and get a clear
                verification outcome without manual back-and-forth.
              </p>
            </div>

            <div
              ref={actionsRef}
              className="flex flex-col items-center gap-4 sm:flex-row lg:justify-start"
            >
              <Link
                href="/verify"
                className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-3 text-white transition-all hover:scale-105 hover:bg-primary/85"
              >
                Start Verification
              </Link>
              <Link
                href="/#features"
                className="inline-flex items-center justify-center rounded-full border border-primary/15 bg-white px-6 py-3 text-foreground transition-colors hover:bg-primary/5"
              >
                Explore Features
              </Link>
            </div>

            <div ref={statsRef} className="grid gap-4 pt-2 sm:grid-cols-3">
              <div className="rounded-3xl border border-foreground/8 bg-white p-4 text-left shadow-[0_18px_40px_-30px_rgba(23,23,23,0.25)]">
                <p className="font-bold text-primary md:text-xl">1 min</p>
                <p className="text-sm text-gray">
                  Average first-pass review time
                </p>
              </div>
              <div className="rounded-3xl border border-foreground/8 bg-white p-4 text-left shadow-[0_18px_40px_-30px_rgba(23,23,23,0.25)]">
                <p className="font-bold text-primary md:text-xl">PDF + Image</p>
                <p className="text-sm text-gray">
                  Supports the formats teams already receive
                </p>
              </div>
              <div className="rounded-3xl border border-foreground/8 bg-white p-4 text-left shadow-[0_18px_40px_-30px_rgba(23,23,23,0.25)]">
                <p className="font-bold text-primary md:text-xl">AI summary</p>
                <p className="text-sm text-gray">
                  Highlights mismatches before escalation
                </p>
              </div>
            </div>
          </div>

          <div ref={visualRef} className="relative mx-auto w-full max-w-xl lg:mx-0">
            <div className="absolute inset-x-10 inset-y-8 -z-10 rounded-4xl bg-primary/12 blur-3xl" />
            <div className="grid gap-5 rounded-4xl border border-foreground/8 bg-white p-4 shadow-[0_36px_90px_-46px_rgba(23,23,23,0.32)] sm:p-5">
              <div className="rounded-xl border border-foreground/8 bg-background/80">
                <div className="flex items-center gap-2 border-b border-foreground/8 px-4 py-3">
                  <span className="h-3 w-3 rounded-full bg-danger" />
                  <span className="h-3 w-3 rounded-full bg-warning" />
                  <span className="h-3 w-3 rounded-full bg-success" />
                  <div className="ml-3 flex-1 rounded-full bg-white px-3 py-1 text-center text-xs text-gray">
                    verifyng-three.vercel.app
                  </div>
                </div>

                <div className="grid gap-4 p-4">
                  <div
                    ref={queueCardRef}
                    className="rounded-3xl border border-foreground/8 bg-white p-4 shadow-[0_18px_40px_-30px_rgba(23,23,23,0.22)]"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-primary/70">
                      Upload queue
                    </p>
                    <div className="mt-3 grid gap-3 rounded-[1.4rem] border border-dashed border-primary/35 bg-primary/5 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold">
                            University Certificate.pdf
                          </p>
                          <p className="text-xs text-gray">
                            Degree certificate uploaded for automated review
                          </p>
                        </div>
                        <div className="rounded-full bg-success-soft px-3 py-1 text-xs font-semibold text-success">
                          Ready
                        </div>
                      </div>
                      <div className="h-2 rounded-full bg-white">
                        <div
                          ref={progressBarRef}
                          className="h-2 w-4/5 rounded-full bg-primary"
                        />
                      </div>
                    </div>
                  </div>

                  <div
                    ref={scoreCardRef}
                    className="rounded-3xl border border-primary/15 bg-primary/8 p-4 shadow-[0_18px_40px_-30px_rgba(0,102,204,0.22)]"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-primary/70">
                          Verification score
                        </p>
                        <p className="mt-2 text-3xl font-bold text-primary">
                          96%
                        </p>
                      </div>
                      <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-primary shadow-sm">
                        Low risk
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-gray">
                      Extracted metadata aligns with institution format and
                      record markers.
                    </p>
                  </div>

                  <div ref={metaGridRef} className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-3xl border border-foreground/8 bg-white p-4 text-center shadow-[0_18px_40px_-30px_rgba(23,23,23,0.22)]">
                      <p className="text-2xl font-bold text-foreground">2019</p>
                      <p className="text-xs uppercase tracking-[0.2em] text-gray">
                        Graduation year
                      </p>
                    </div>
                    <div className="rounded-3xl border border-foreground/8 bg-white p-4 text-center shadow-[0_18px_40px_-30px_rgba(23,23,23,0.22)]">
                      <p className="text-2xl font-bold text-foreground">B.Sc</p>
                      <p className="text-xs uppercase tracking-[0.2em] text-gray">
                        Award
                      </p>
                    </div>
                    <div className="rounded-3xl border border-foreground/8 bg-white p-4 text-center shadow-[0_18px_40px_-30px_rgba(23,23,23,0.22)]">
                      <p className="text-2xl font-bold text-foreground">
                        1 flag
                      </p>
                      <p className="text-xs uppercase tracking-[0.2em] text-gray">
                        Needs review
                      </p>
                    </div>
                  </div>

                  <div
                    ref={noteCardRef}
                    className="rounded-3xl border border-foreground/8 bg-white px-4 py-3 text-sm text-gray shadow-[0_18px_40px_-30px_rgba(23,23,23,0.22)]"
                  >
                    <p className="font-medium text-foreground">
                      Ask VerifyNG for a review summary
                    </p>
                    <p className="mt-2 flex min-h-11 items-center gap-1.5 text-sm text-gray">
                      <span ref={typingTextRef} />
                      <span
                        ref={typingCursorRef}
                        aria-hidden="true"
                        className="inline-block h-4 w-px bg-primary"
                      />
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
