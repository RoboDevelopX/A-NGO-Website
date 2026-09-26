import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { formatDate, getEvent, site } from "@/lib/content";
import { Media } from "@/components/Media";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return site.events.map((e) => ({ slug: e.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const event = getEvent((await params).slug);
  return event ? { title: event.title, description: event.summary } : {};
}

export default async function EventPage({ params }: Props) {
  const event = getEvent((await params).slug);
  if (!event) notFound();
  const isPast = new Date(event.endDate ?? event.date) < new Date();

  return (
    <article className="section">
      <div className="container container--narrow">
        <Link href="/events" className="text-link">
          <span aria-hidden="true">←</span> All events
        </Link>
        <h1 className="mt-sm">{event.title}</h1>
        <dl className="event-facts">
          <div>
            <dt>When</dt>
            <dd>
              <time dateTime={event.date}>{formatDate(event.date, true)}</time>
              {event.endDate && ` to ${new Date(event.endDate).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}`}
            </dd>
          </div>
          <div>
            <dt>Where</dt>
            <dd>{event.location}</dd>
          </div>
        </dl>
        {isPast && <p className="notice notice--info">This event has already taken place.</p>}
        <Media src={event.image} alt={event.imageAlt} label={event.title} className="article__media" />
        <div className="prose">
          <p className="lead-sm">{event.summary}</p>
          {event.body.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
        {!isPast && event.ctaHref && (
          <Link href={event.ctaHref} className="btn btn--primary btn--lg">
            {event.ctaLabel ?? "Get involved"}
          </Link>
        )}
      </div>
    </article>
  );
}
