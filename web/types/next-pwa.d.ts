declare module "next-pwa" {
  type PwaPlugin = <T>(nextConfig?: T) => T;

  export default function nextPwa(options?: Record<string, unknown>): PwaPlugin;
}
