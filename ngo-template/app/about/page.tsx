import type { Metadata } from "next";
import Link from "next/link";
import { site } from "@/lib/content";
import { Media } from "@/components/Media";
import { PageHeader } from "@/components/PageHeader";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  const { organization: org, about, programs } = site;
  return (
    <>
      <PageHeader eyebrow={`Since ${org.foundedYear}`} title={`About ${org.shortName}`} intro={org.mission} />

      <section className="section">
        <div className="container split">
          <div className="prose">
            <h2>Our story</h2>
            {about.story.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
            <blockquote className="vision">
              <span className="eyebrow">Our vision</span>
              {org.vision}
            </blockquote>
          </div>
          <Media label="Team in the field" className="split__media" />
        </div>
      </section>

      <section className="section section--alt">
        <div className="container">
          <h2>What we value</h2>
          <div className="grid grid--3">
            {about.values.map((v) => (
              <div key={v.title} className="value">
                <h3>{v.title}</h3>
                <p>{v.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>Our programmes</h2>
          <div className="stack stack--lg">
            {programs.map((p, i) => (
              <article key={p.slug} id={p.slug} className={`program ${i % 2 ? "program--reverse" : ""}`}>
                <Media src={p.image} alt={p.imageAlt} label={p.title} className="program__media" />
                <div>
                  <h3>{p.title}</h3>
                  <p className="lead-sm">{p.summary}</p>
                  <p>{p.details}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section--alt">
        <div className="container">
          <h2>Our team</h2>
          <div className="grid grid--4">
            {about.team.map((m) => (
              <div key={m.name} className="person">
                <Media src={m.image} alt={m.imageAlt ?? m.name} label={m.name} className="person__photo" />
                <h3>{m.name}</h3>
                <p className="muted">{m.role}</p>
              </div>
            ))}
          </div>
          {about.partners.length > 0 && (
            <>
              <h3 className="partners__title">With thanks to our partners</h3>
              <ul className="partners">
                {about.partners.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      </section>

      <section className="cta-band">
        <div className="container cta-band__inner">
          <h2>Help us reach the next village.</h2>
          <div className="btn-row">
            <Link href="/donate" className="btn btn--accent btn--lg">
              Donate
            </Link>
            <Link href="/get-involved" className="btn btn--outline-light btn--lg">
              Volunteer
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
