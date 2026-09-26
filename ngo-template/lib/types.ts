export interface Link {
  label: string;
  href: string;
}

export interface ImageRef {
  /** Path under /public (e.g. "/images/hero.jpg") or a full URL. Empty = placeholder. */
  image?: string;
  imageAlt?: string;
}

export interface Program extends ImageRef {
  slug: string;
  title: string;
  summary: string;
  details: string;
}

export interface EventItem extends ImageRef {
  slug: string;
  title: string;
  /** ISO date-time, local to the organisation. */
  date: string;
  endDate?: string;
  location: string;
  summary: string;
  body: string[];
  ctaLabel?: string;
  ctaHref?: string;
}

export interface BlogPost extends ImageRef {
  slug: string;
  title: string;
  /** ISO date. */
  date: string;
  author: string;
  excerpt: string;
  body: string[];
  tags?: string[];
}

export interface SiteConfig {
  organization: {
    name: string;
    shortName: string;
    tagline: string;
    mission: string;
    vision: string;
    foundedYear: number;
    registrationNumber?: string;
    /** Two or three letters shown in the logo mark. */
    logoText: string;
  };
  theme: {
    primary: string;
    primaryContrast: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    muted: string;
    fontHeading: string;
    fontBody: string;
  };
  contact: {
    email: string;
    phone?: string;
    address?: string;
    officeHours?: string;
    social: { label: string; url: string }[];
  };
  navigation: Link[];
  home: {
    hero: ImageRef & {
      heading: string;
      subheading: string;
      primaryCta: Link;
      secondaryCta?: Link;
    };
    stats: { value: string; label: string }[];
    closingCta: {
      heading: string;
      body: string;
      primaryCta: Link;
      secondaryCta?: Link;
    };
  };
  about: {
    story: string[];
    values: { title: string; body: string }[];
    team: ({ name: string; role: string } & ImageRef)[];
    partners: string[];
  };
  programs: Program[];
  donate: {
    intro: string;
    currency: string;
    currencySymbol: string;
    presetAmounts: { amount: number; impact: string }[];
    otherWays: { title: string; body: string }[];
    taxNote?: string;
  };
  getInvolved: {
    intro: string;
    volunteerRoles: string[];
    availabilityOptions: string[];
  };
  events: EventItem[];
  blog: BlogPost[];
  footer: { note: string };
}
