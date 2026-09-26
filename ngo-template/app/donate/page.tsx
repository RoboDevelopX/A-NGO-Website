import type { Metadata } from "next";
import { site } from "@/lib/content";
import { PageHeader } from "@/components/PageHeader";
import { DonateForm } from "@/components/DonateForm";

export const metadata: Metadata = { title: "Donate" };

export default function DonatePage() {
  const { donate, contact } = site;
  return (
    <>
      <PageHeader eyebrow="Donate" title="Your gift goes further than you think" intro={donate.intro} />
      <section className="section">
        <div className="container split split--form">
          <div>
            <h2>What your gift does</h2>
            <ul className="impact-list">
              {donate.presetAmounts.map((p) => (
                <li key={p.amount}>
                  <span className="impact-list__amount">
                    {donate.currencySymbol}
                    {p.amount}
                  </span>
                  <span>{p.impact}</span>
                </li>
              ))}
            </ul>
            {donate.taxNote && <p className="muted small">{donate.taxNote}</p>}
          </div>
          <div className="panel">
            <h2>Give online</h2>
            <DonateForm presets={donate.presetAmounts} currencySymbol={donate.currencySymbol} />
          </div>
        </div>
      </section>
      <section className="section section--alt">
        <div className="container">
          <h2>Other ways to give</h2>
          <div className="grid grid--2">
            {donate.otherWays.map((w) => (
              <div key={w.title} className="value">
                <h3>{w.title}</h3>
                <p>{w.body}</p>
              </div>
            ))}
          </div>
          <p className="muted">
            Questions about giving? Email <a href={`mailto:${contact.email}`}>{contact.email}</a>.
          </p>
        </div>
      </section>
    </>
  );
}
