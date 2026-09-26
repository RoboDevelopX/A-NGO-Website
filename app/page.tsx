import Link from "next/link";
import { getEvents, getPosts, site } from "@/lib/content";
import { Media } from "@/components/Media";
import { EventCard, PostCard, ProgramCard } from "@/components/Cards";

// Re-evaluate which events are upcoming at most hourly.
export const revalidate = 3600;

export default function HomePage() {
  const { hero, stats, closingCta } = site.home;
  const { upcoming } = getEvents();
  const posts = getPosts().slice(0, 3);

  return (
    <>
      <section className="hero">
        <div className="container hero__grid">
          <div className="hero__copy">
            <p className="eyebrow">{site.organization.name}</p>
            <h1>{hero.heading}</h1>
            <p className="lead">{hero.subheading}</p>
            <div className="btn-row">
              <Link href={hero.primaryCta.href} className="btn btn--accent btn--lg">
                {hero.primaryCta.label}
              </Link>
              {hero.secondaryCta && (
                <Link href={hero.secondaryCta.href} className="btn btn--outline-light btn--lg">
                  {hero.secondaryCta.label}
                </Link>
              )}
            </div>
          </div>
          <Media src={hero.image} alt={hero.imageAlt} label="Hero photo" className="hero__media" priority />
        </div>
      </section>

      <section className="section section--tight">
        <div className="container mission">
          <p className="eyebrow">Our mission</p>
          <p className="mission__text">{site.organization.mission}</p>
          <Link href="/about" className="text-link">
            Read our story <span aria-hidden="true">→</span>
          </Link>
        </div>
      </section>

      <section className="stats" aria-label="Our impact">
        <div className="container stats__grid">
          {stats.map((s) => (
            <div key={s.label} className="stat">
              <span className="stat__value">{s.value}</span>
              <span className="stat__label">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section__head">
            <h2>What we do</h2>
            <Link href="/about" className="text-link">
              All programmes <span aria-hidden="true">→</span>
            </Link>
          </div>
          <div className="grid grid--3">
            {site.programs.map((p) => (
              <ProgramCard key={p.slug} program={p} />
            ))}
          </div>
        </div>
      </section>

      {upcoming.length > 0 && (
        <section className="section section--alt">
          <div className="container">
            <div className="section__head">
              <h2>Upcoming events</h2>
              <Link href="/events" className="text-link">
                All events <span aria-hidden="true">→</span>
              </Link>
            </div>
            <div className="stack">
              {upcoming.slice(0, 3).map((e) => (
                <EventCard key={e.slug} event={e} />
              ))}
            </div>
          </div>
        </section>
      )}

      {posts.length > 0 && (
        <section className="section">
          <div className="container">
            <div className="section__head">
              <h2>Latest stories</h2>
              <Link href="/blog" className="text-link">
                Read the blog <span aria-hidden="true">→</span>
              </Link>
            </div>
            <div className="grid grid--3">
              {posts.map((p) => (
                <PostCard key={p.slug} post={p} />
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="cta-band">
        <div className="container cta-band__inner">
          <div>
            <h2>{closingCta.heading}</h2>
            <p>{closingCta.body}</p>
          </div>
          <div className="btn-row">
            <Link href={closingCta.primaryCta.href} className="btn btn--accent btn--lg">
              {closingCta.primaryCta.label}
            </Link>
            {closingCta.secondaryCta && (
              <Link href={closingCta.secondaryCta.href} className="btn btn--outline-light btn--lg">
                {closingCta.secondaryCta.label}
              </Link>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
