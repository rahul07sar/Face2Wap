/**
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        layout.tsx
 * Module:      Web / App Layout
 * Description:
 *
 * Defines the root layout for the Face2Wap Next.js application without
 * external font fetching, keeping Docker builds stable in local development.
 *
 * ============================================================================
 */

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Face2Wap",
  description: "Open image and video face swap tool.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}