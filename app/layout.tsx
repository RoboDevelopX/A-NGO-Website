import type { Metadata } from "next";
import type { CSSProperties, ReactNode } from "react";
import { site } from "@/lib/content";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: site.organization.name, template: `%s · ${site.organization.name}` },
  description: site.organization.mission,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const t = site.theme;
  // Theme colours from site.config.ts become CSS variables used throughout globals.css.
  const themeVars = {
    "--color-primary": t.primary,
    "--color-primary-contrast": t.primaryContrast,
    "--color-accent": t.accent,
    "--color-bg": t.background,
    "--color-surface": t.surface,
    "--color-text": t.text,
    "--color-muted": t.muted,
    "--font-heading": t.fontHeading,
    "--font-body": t.fontBody,
  } as CSSProperties;

  return (
    <html lang="en" style={themeVars}>
      <body>
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <Header name={site.organization.name} logoText={site.organization.logoText} navigation={site.navigation} />
        <main id="main">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
