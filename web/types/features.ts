import type { ComponentType, SVGProps } from "react";

export interface Features {
  title: string;
  description: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}
