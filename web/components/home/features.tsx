"use client";

import { useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { features } from "@/constants/general";

gsap.registerPlugin(ScrollTrigger);

const Features = () => {
  const sectionRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (reduceMotion.matches || !sectionRef.current) {
      return;
    }

    const heading = sectionRef.current.querySelector("[data-features-heading]");
    const cards = sectionRef.current.querySelectorAll("[data-feature-card]");

    const ctx = gsap.context(() => {
      gsap.fromTo(
        heading,
        { y: 28, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 82%",
            once: true,
          },
        }
      );

      gsap.fromTo(
        cards,
        { y: 34, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.65,
          ease: "power3.out",
          stagger: 0.12,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 78%",
            once: true,
          },
        }
      );

      ScrollTrigger.refresh();
    }, sectionRef);

    return () => {
      ctx.revert();
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      id="features"
      className="app-container scroll-mt-28"
    >
      <div className="mt-14 grid gap-6 pb-10">
        <h2
          data-features-heading
          className="text-center text-4xl font-extrabold md:text-4xl"
        >
          Verify your Certificate
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 py-5">
          {features.map((feature) => (
            <div
              key={feature.title}
              data-feature-card
              className="grid gap-3 rounded-2xl border border-gray/40 bg-white p-5 shadow-[0_18px_40px_-28px_rgba(23,23,23,0.28),0_10px_18px_-18px_rgba(0,102,204,0.22)] transition-all duration-300 hover:-translate-y-1 hover:border-primary/20 hover:shadow-[0_26px_55px_-30px_rgba(23,23,23,0.32),0_18px_28px_-22px_rgba(0,102,204,0.28)]"
            >
              <feature.icon className="h-8 w-8 text-primary" />
              <h2 className="text-xl font-bold">{feature.title}</h2>
              <p className="text-sm text-gray">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
