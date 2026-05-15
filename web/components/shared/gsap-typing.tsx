"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";

gsap.registerPlugin(TextPlugin);

interface GsapTypingProps {
  messages?: string[];
}

const GsapTyping = ({
  messages = [
    "Getting stuff from server...",
    "Running pipeline...",
    "Analyzing document...",
    "Almost there...",
  ],
}: GsapTypingProps) => {
  const el = useRef<HTMLSpanElement | null>(null);
  const index = useRef(0);

  useEffect(() => {
    let cancelled = false;

    const typeNext = () => {
      if (cancelled || !el.current) return;

      const msg = messages[index.current % messages.length];
      const typeDuration = Math.max(0.6, msg.length * 0.05);
      const eraseDuration = Math.max(0.3, msg.length * 0.03);

      gsap.killTweensOf(el.current);

      gsap.to(el.current, {
        duration: typeDuration,
        text: msg,
        ease: "none",
        onComplete: () => {
          if (cancelled) return;
          gsap.delayedCall(1.0, () => {
            if (cancelled || !el.current) return;
            gsap.to(el.current, {
              duration: eraseDuration,
              text: "",
              ease: "none",
              onComplete: () => {
                if (cancelled) return;
                index.current += 1;
                typeNext();
              },
            });
          });
        },
      });
    };

    typeNext();

    return () => {
      cancelled = true;
      if (el.current) gsap.killTweensOf(el.current);
    };
  }, [messages]);

  return (
    <p className="mt-2 text-sm text-foreground/75">
      <span ref={el} />
      <span className="ml-2 inline-block animate-pulse">|</span>
    </p>
  );
};

export default GsapTyping;
