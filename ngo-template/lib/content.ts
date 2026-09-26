import siteConfig from "@/site.config";
import type { BlogPost, EventItem } from "./types";

export const site = siteConfig;

/** Events split into upcoming (soonest first) and past (latest first). */
export function getEvents(now: Date = new Date()) {
  const sorted = [...site.events].sort((a, b) => a.date.localeCompare(b.date));
  const isPast = (e: EventItem) => new Date(e.endDate ?? e.date) < now;
  return {
    upcoming: sorted.filter((e) => !isPast(e)),
    past: sorted.filter(isPast).reverse(),
  };
}

export function getEvent(slug: string): EventItem | undefined {
  return site.events.find((e) => e.slug === slug);
}

export function getPosts(): BlogPost[] {
  return [...site.blog].sort((a, b) => b.date.localeCompare(a.date));
}

export function getPost(slug: string): BlogPost | undefined {
  return site.blog.find((p) => p.slug === slug);
}

export function formatDate(iso: string, withTime = false): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    weekday: withTime ? "short" : undefined,
    year: "numeric",
    month: "long",
    day: "numeric",
    ...(withTime ? { hour: "numeric", minute: "2-digit" } : {}),
  });
}
