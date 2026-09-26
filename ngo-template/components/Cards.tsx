import Link from "next/link";
import { formatDate } from "@/lib/content";
import type { BlogPost, EventItem, Program } from "@/lib/types";
import { Media } from "./Media";

export function ProgramCard({ program }: { program: Program }) {
  return (
    <article className="card">
      <Media src={program.image} alt={program.imageAlt} label={program.title} className="card__media" />
      <div className="card__body">
        <h3>{program.title}</h3>
        <p>{program.summary}</p>
        <Link href={`/about#${program.slug}`} className="text-link">
          How it works <span aria-hidden="true">→</span>
        </Link>
      </div>
    </article>
  );
}

export function EventCard({ event, past = false }: { event: EventItem; past?: boolean }) {
  const d = new Date(event.date);
  return (
    <article className={`card card--row ${past ? "card--past" : ""}`}>
      <div className="date-badge" aria-hidden="true">
        <span className="date-badge__month">{d.toLocaleDateString("en-US", { month: "short" })}</span>
        <span className="date-badge__day">{d.getDate()}</span>
      </div>
      <div className="card__body">
        <h3>
          <Link href={`/events/${event.slug}`}>{event.title}</Link>
        </h3>
        <p className="meta">
          <time dateTime={event.date}>{formatDate(event.date, true)}</time> · {event.location}
        </p>
        <p>{event.summary}</p>
      </div>
    </article>
  );
}

export function PostCard({ post }: { post: BlogPost }) {
  return (
    <article className="card">
      <Media src={post.image} alt={post.imageAlt} label={post.title} className="card__media" />
      <div className="card__body">
        <p className="meta">
          <time dateTime={post.date}>{formatDate(post.date)}</time> · {post.author}
        </p>
        <h3>
          <Link href={`/blog/${post.slug}`}>{post.title}</Link>
        </h3>
        <p>{post.excerpt}</p>
      </div>
    </article>
  );
}
