import type { Metadata } from "next";
import { site } from "@/lib/content";
import { PageHeader } from "@/components/PageHeader";
import { GetInvolvedForm } from "@/components/GetInvolvedForm";

export const metadata: Metadata = { title: "Get involved" };

export default async function GetInvolvedPage({
  searchParams,
}: {
  searchParams: Promise<{ type?: string }>;
}) {
  const { type } = await searchParams;
  const { getInvolved, contact } = site;
  return (
    <>
      <PageHeader eyebrow="Get involved" title="Volunteer or get in touch" intro={getInvolved.intro} />
      <section className="section">
        <div className="container split split--form">
          <aside className="contact-card">
            <h2>Contact details</h2>
            <dl>
              <dt>Email</dt>
              <dd>
                <a href={`mailto:${contact.email}`}>{contact.email}</a>
              </dd>
              {contact.phone && (
                <>
                  <dt>Phone</dt>
                  <dd>{contact.phone}</dd>
                </>
              )}
              {contact.address && (
                <>
                  <dt>Address</dt>
                  <dd>{contact.address}</dd>
                </>
              )}
              {contact.officeHours && (
                <>
                  <dt>Office hours</dt>
                  <dd>{contact.officeHours}</dd>
                </>
              )}
            </dl>
            <h3>Ways to volunteer</h3>
            <ul className="tick-list">
              {getInvolved.volunteerRoles.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </aside>
          <div className="panel">
            <GetInvolvedForm
              roles={getInvolved.volunteerRoles}
              availabilityOptions={getInvolved.availabilityOptions}
              initialKind={type === "contact" ? "contact" : "volunteer"}
              contactEmail={contact.email}
            />
          </div>
        </div>
      </section>
    </>
  );
}
