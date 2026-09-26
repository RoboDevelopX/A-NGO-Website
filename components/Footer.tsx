import Link from "next/link";
import { site } from "@/lib/content";

export function Footer() {
  const { organization: org, contact, navigation, footer } = site;
  return (
    <footer className="site-footer">
      <div className="container site-footer__grid">
        <div>
          <p className="site-footer__name">{org.name}</p>
          <p>{org.tagline}</p>
          {org.registrationNumber && <p className="muted small">{org.registrationNumber}</p>}
        </div>
        <div>
          <h2 className="site-footer__heading">Explore</h2>
          <ul className="plain-list">
            {navigation.map((n) => (
              <li key={n.href}>
                <Link href={n.href}>{n.label}</Link>
              </li>
            ))}
            <li>
              <Link href="/donate">Donate</Link>
            </li>
          </ul>
        </div>
        <div>
          <h2 className="site-footer__heading">Contact</h2>
          <ul className="plain-list">
            <li>
              <a href={`mailto:${contact.email}`}>{contact.email}</a>
            </li>
            {contact.phone && (
              <li>
                <a href={`tel:${contact.phone.replace(/[^+\d]/g, "")}`}>{contact.phone}</a>
              </li>
            )}
            {contact.address && <li>{contact.address}</li>}
            {contact.officeHours && <li className="muted">{contact.officeHours}</li>}
          </ul>
        </div>
        <div>
          <h2 className="site-footer__heading">Follow</h2>
          <ul className="plain-list">
            {contact.social.map((s) => (
              <li key={s.url}>
                <a href={s.url} target="_blank" rel="noopener noreferrer">
                  {s.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="container site-footer__bottom">
        <p>
          © {new Date().getFullYear()} {org.name}. {footer.note}
        </p>
      </div>
    </footer>
  );
}
