"use client";

import { useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ChatBubbleBottomCenterTextIcon,
  CpuChipIcon,
  ClipboardDocumentCheckIcon,
} from "@heroicons/react/24/outline";

gsap.registerPlugin(ScrollTrigger);

const steps = [
  {
    id: "Step 01",
    title: "Upload the certificate",
    description:
      "Drop in the candidate document and let VerifyNG prepare it for structured analysis.",
    note: "PDF or image accepted",
    icon: ChatBubbleBottomCenterTextIcon,
    accent: "bg-primary/10 text-primary",
  },
  {
    id: "Step 02",
    title: "We analyze the details",
    description:
      "The system extracts metadata, checks formatting signals, and flags inconsistencies that deserve attention.",
    note: "AI pattern review",
    icon: CpuChipIcon,
    accent: "bg-warning-soft text-warning",
  },
  {
    id: "Step 03",
    title: "You get a clear verdict",
    description:
      "Review the outcome, confidence signals, and summary notes before making the final decision.",
    note: "Decision-ready summary",
    icon: ClipboardDocumentCheckIcon,
    accent: "bg-success-soft text-success",
  },
];

const Step = () => {
  const sectionRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (reduceMotion.matches || !sectionRef.current) {
      return;
    }

    const heading = sectionRef.current.querySelector("[data-step-heading]");
    const subheading = sectionRef.current.querySelector("[data-step-subheading]");
    const cards = sectionRef.current.querySelectorAll("[data-step-card]");
    const rail = sectionRef.current.querySelector("[data-step-rail]");
    const markers = sectionRef.current.querySelectorAll("[data-step-marker]");

    const ctx = gsap.context(() => {
      gsap.fromTo(
        [heading, subheading],
        { y: 28, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          ease: "power3.out",
          stagger: 0.12,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 78%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        rail,
        { scaleX: 0, transformOrigin: "left center" },
        {
          scaleX: 1,
          duration: 0.9,
          ease: "power2.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 72%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        markers,
        { scale: 0.4, opacity: 0 },
        {
          scale: 1,
          opacity: 1,
          duration: 0.4,
          ease: "back.out(2.4)",
          stagger: 0.14,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 72%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        cards,
        { y: 38, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          ease: "power3.out",
          stagger: 0.14,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 68%",
            once: true,
          },
        }
      );

      gsap.to(cards, {
        y: -8,
        duration: 2.4,
        ease: "sine.inOut",
        stagger: {
          each: 0.18,
          from: "center",
          yoyo: true,
          repeat: -1,
        },
        repeat: -1,
        yoyo: true,
      });
    }, sectionRef);

    return () => {
      ctx.revert();
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      id="process"
      className="app-container scroll-mt-28 py-16 md:py-24 grid gap-8"
    >
      <h2
        data-features-heading
        className="text-center text-4xl font-extrabold md:text-4xl"
      >
        Features
      </h2>
      <div className="relative overflow-hidden rounded-4xl border border-foreground/8 px-6 py-10 shadow-[0_36px_90px_-52px_rgba(23,23,23,0.65)] md:px-10 md:py-14">
        <div
          aria-hidden="true"
          className="absolute inset-0 opacity-70"
        />

        <div className="relative grid gap-10">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
            <div className="grid gap-4">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-primary/80">
                The Process
              </p>
              <h2
                data-step-heading
                className="max-w-3xl text-4xl font-bold tracking-tight md:text-5xl"
              >
                Three steps.
                <br />
                Minutes to clarity.
                <span className="text-primary italic"> One verification flow.</span>
              </h2>
            </div>
            <p
              data-step-subheading
              className="text-sm uppercase tracking-[0.3em] text-background/55"
            >
              Fast review • clear output • less guesswork
            </p>
          </div>

          <div className="relative hidden lg:block">
            <div
              data-step-rail
              className="absolute left-[12%] right-[12%] top-1/2 h-px -translate-y-1/2 bg-linear-to-r from-primary/20 via-primary/65 to-primary/20"
            />
            <div className="grid grid-cols-3 px-[12%]">
              {steps.map((step) => (
                <div key={step.id} className="flex justify-center">
                  <span
                    data-step-marker
                    className="h-3 w-3 rounded-full border border-primary/50 shadow-[0_0_0_8px_rgba(0,102,204,0.12)]"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-3 lg:gap-0">
            {steps.map((step, index) => (
              <article
                key={step.id}
                data-step-card
                className="relative grid gap-5 border border-background/10 bg-white/4 p-6 backdrop-blur-sm lg:min-h-80 lg:border-y-0 lg:p-7"
              >
                <div className="flex items-start justify-between gap-4">
                  <span className="rounded-full bg-primary/12 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-primary">
                    {step.id}
                  </span>
                  <span
                    className={`inline-flex h-11 w-11 items-center justify-center rounded-2xl ${step.accent}`}
                  >
                    <step.icon className="h-6 w-6" />
                  </span>
                </div>

                <div className="grid gap-3">
                  <h3 className="max-w-xs text-2xl font-bold ">
                    {step.title}
                  </h3>
                  <p className="max-w-sm text-base leading-7 text-gray">
                    {step.description}
                  </p>
                </div>

                <div className="mt-auto flex items-center justify-between gap-3 border-t border-background/10 pt-4">
                  <span className="text-sm text-background/60">{step.note}</span>
                  <span className="text-sm font-semibold text-primary">
                    0{index + 1}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Step;
