import {
  BanknotesIcon,
  BoltIcon,
  CheckBadgeIcon,
  DocumentMagnifyingGlassIcon,
  ShieldCheckIcon,
  UserGroupIcon,
} from "@heroicons/react/24/outline";
import type { Features } from "@/types/features";

export const features: Features[] = [
  {
    title: "Deep Certificate Analysis",
    description:
      "Review each certificate with structured insights that highlight issuing institution details, credential patterns, and signals that need closer human attention.",
    icon: DocumentMagnifyingGlassIcon,
  },
  {
    title: "Fast Verification Turnaround",
    description:
      "Move from upload to verification outcome in minutes, reducing the long email chains and manual back-and-forth that usually delay candidate screening.",
    icon: BoltIcon,
  },
  {
    title: "Fraud Risk Detection",
    description:
      "Flag suspicious edits, unusual formatting, and missing validation signals early so your team can focus its effort on the highest-risk submissions first.",
    icon: ShieldCheckIcon,
  },
  {
    title: "Affordable Per-Certificate Pricing",
    description:
      "Start verification at a cost that works for growing teams, with transparent pricing that makes routine credential checks easy to scale.",
    icon: BanknotesIcon,
  },
  {
    title: "Employer-Ready Reports",
    description:
      "Generate clear verification summaries your HR, compliance, or admissions team can review quickly and use confidently in decision-making.",
    icon: CheckBadgeIcon,
  },
  {
    title: "Built for Hiring Teams",
    description:
      "Designed for recruiters, HR teams, and institutions that need a reliable workflow for handling multiple certificate checks without operational friction.",
    icon: UserGroupIcon,
  },
];
