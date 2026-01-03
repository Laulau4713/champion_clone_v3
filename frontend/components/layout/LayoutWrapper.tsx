"use client";

import { usePathname } from "next/navigation";
import { Header } from "./Header";
import { Footer } from "./Footer";

interface LayoutWrapperProps {
  children: React.ReactNode;
}

// Routes where we hide header/footer for immersive experience
const IMMERSIVE_ROUTES = ["/training/session/"];

export function LayoutWrapper({ children }: LayoutWrapperProps) {
  const pathname = usePathname();

  // Check if current route should be immersive (no header/footer)
  const isImmersive = IMMERSIVE_ROUTES.some((route) => pathname.startsWith(route));

  if (isImmersive) {
    return <main className="h-screen">{children}</main>;
  }

  return (
    <>
      <Header />
      <main className="flex-1 pt-24">{children}</main>
      <Footer />
    </>
  );
}
