import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { ScrollToTop } from "@/components/layout/ScrollToTop";
import { LayoutWrapper } from "@/components/layout/LayoutWrapper";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Champion Clone - AI Sales Training",
  description:
    "Clone your sales champions with AI. Train your team with real voices and proven patterns.",
  keywords: ["sales training", "AI", "voice cloning", "sales coaching"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="dark">
      <body className={`${inter.className} min-h-screen flex flex-col`}>
        <Providers>
          <ScrollToTop />
          <LayoutWrapper>{children}</LayoutWrapper>
        </Providers>
      </body>
    </html>
  );
}
