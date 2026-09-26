/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  SITE CONFIG — the only file most NGOs need to edit.
 *
 *  Everything organisation-specific lives here: name, mission, colours,
 *  photos, programmes, team, donation options, events, blog posts and the
 *  volunteer roles offered on the contact form. Pages read from this object;
 *  none of them hard-code content.
 *
 *  Images: put files in /public/images and reference them as "/images/x.jpg".
 *  Leave `image` empty and a branded placeholder is rendered instead.
 *
 *  The sample content below describes a fictional organisation.
 * ─────────────────────────────────────────────────────────────────────────────
 */
import type { SiteConfig } from "@/lib/types";

const siteConfig: SiteConfig = {
  organization: {
    name: "Brightpath Foundation",
    shortName: "Brightpath",
    tagline: "Opening doors through education, clean water and community health.",
    mission:
      "We partner with rural communities so every child can learn, every family has safe water, and every village can care for its own health.",
    vision: "A world where where you are born no longer decides how far you can go.",
    foundedYear: 2012,
    registrationNumber: "Reg. Charity No. 000000 (sample)",
    logoText: "BP",
  },

  theme: {
    primary: "#0f766e",
    primaryContrast: "#ffffff",
    accent: "#f59e0b",
    background: "#fbfaf7",
    surface: "#ffffff",
    text: "#1f2937",
    muted: "#6b7280",
    fontHeading: "Georgia, 'Times New Roman', serif",
    fontBody: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  },

  contact: {
    email: "hello@brightpath.example.org",
    phone: "+1 (555) 010-2030",
    address: "12 Riverside Lane, Springfield",
    officeHours: "Mon to Fri, 9am to 5pm",
    social: [
      { label: "Instagram", url: "https://instagram.com/" },
      { label: "Facebook", url: "https://facebook.com/" },
      { label: "LinkedIn", url: "https://linkedin.com/" },
    ],
  },

  navigation: [
    { label: "Home", href: "/" },
    { label: "About", href: "/about" },
    { label: "Events", href: "/events" },
    { label: "Blog", href: "/blog" },
    { label: "Get involved", href: "/get-involved" },
  ],

  home: {
    hero: {
      heading: "Every child deserves a path forward.",
      subheading:
        "Brightpath works alongside 40 rural communities to build schools, bring clean water and train local health workers.",
      image: "",
      imageAlt: "Children walking to school along a village road",
      primaryCta: { label: "Donate now", href: "/donate" },
      secondaryCta: { label: "Volunteer with us", href: "/get-involved" },
    },
    stats: [
      { value: "12,400+", label: "children in school" },
      { value: "86", label: "wells built" },
      { value: "40", label: "partner villages" },
      { value: "92%", label: "of funds go to programmes" },
    ],
    closingCta: {
      heading: "Your time or a small gift can change a life this year.",
      body: "Join thousands of supporters who keep our programmes running.",
      primaryCta: { label: "Give today", href: "/donate" },
      secondaryCta: { label: "Become a volunteer", href: "/get-involved" },
    },
  },

  about: {
    story: [
      "Brightpath began in 2012 when a group of teachers raised money to repair one flooded classroom. The village asked for more than a roof: they wanted a say in how their children learned.",
      "That idea still guides us. Every project starts with a community meeting, is led by local staff, and is handed over to the village once it can run on its own.",
    ],
    values: [
      { title: "Community-led", body: "Villages choose the projects and own them when we step back." },
      { title: "Transparent", body: "We publish our accounts every year and report on every project." },
      { title: "Lasting", body: "We build what can be maintained locally, long after we leave." },
    ],
    team: [
      { name: "Amara Okafor", role: "Executive Director", image: "" },
      { name: "Daniel Reyes", role: "Head of Programmes", image: "" },
      { name: "Priya Nair", role: "Community Health Lead", image: "" },
      { name: "Tomás Silva", role: "Volunteer Coordinator", image: "" },
    ],
    partners: ["Springfield Rotary Club", "Clear Water Trust", "County Education Board"],
  },

  programs: [
    {
      slug: "education",
      title: "Education",
      summary: "Classrooms, trained teachers and school supplies for children who would otherwise miss out.",
      details:
        "We build and repair classrooms, fund teacher training and provide books and uniforms so cost is never the reason a child stays home.",
      image: "",
    },
    {
      slug: "clean-water",
      title: "Clean water",
      summary: "Wells and filtration systems that cut the walk for water from hours to minutes.",
      details:
        "Each well is sited with the community, built by local crews and maintained by a trained village water committee.",
      image: "",
    },
    {
      slug: "health",
      title: "Community health",
      summary: "Local health workers trained to treat common illness and support mothers and newborns.",
      details:
        "We train and equip community health workers who provide first-line care, run vaccination days and refer serious cases to clinics.",
      image: "",
    },
  ],

  donate: {
    intro:
      "Every gift goes straight to our programmes. Choose an amount below, or use one of the other ways to give.",
    currency: "USD",
    currencySymbol: "$",
    presetAmounts: [
      { amount: 25, impact: "School supplies for one child for a year" },
      { amount: 50, impact: "Trains a community health worker for a month" },
      { amount: 100, impact: "Clean water for a family for five years" },
      { amount: 250, impact: "Furnishes a classroom with desks and books" },
    ],
    otherWays: [
      {
        title: "Bank transfer",
        body: "Brightpath Foundation · Account 00000000 · Sort code 00-00-00 (sample details). Please use your email as the reference.",
      },
      {
        title: "Cheque",
        body: "Make cheques payable to “Brightpath Foundation” and post them to our office address.",
      },
      {
        title: "In-kind gifts",
        body: "We accept books, laptops and medical supplies. Contact us first so we can confirm what is needed.",
      },
      {
        title: "Fundraise for us",
        body: "Run, bake or cycle for Brightpath. Get in touch and we will send you a fundraising pack.",
      },
    ],
    taxNote: "Donations may be tax deductible. A receipt is emailed for every gift.",
  },

  getInvolved: {
    intro:
      "Whether you have an afternoon or a year, there is a way to help. Tell us a little about yourself and we will be in touch within a few days.",
    volunteerRoles: [
      "Event support",
      "Fundraising",
      "Tutoring and mentoring",
      "Photography and media",
      "Office and admin",
      "Skilled / professional",
    ],
    availabilityOptions: ["Weekdays", "Evenings", "Weekends", "Flexible"],
  },

  events: [
    {
      slug: "charity-fun-run-2026",
      title: "Brightpath Charity Fun Run",
      date: "2026-10-18T09:00:00",
      endDate: "2026-10-18T13:00:00",
      location: "Springfield Riverside Park",
      summary: "A 5k run and walk for all ages, raising money for two new village wells.",
      body: [
        "Join hundreds of runners, walkers and families for our annual fun run. Every registration funds clean water.",
        "Registration opens at 8am. Water stations, face painting and a finish-line picnic are included.",
      ],
      image: "",
      ctaLabel: "Volunteer at the event",
      ctaHref: "/get-involved",
    },
    {
      slug: "volunteer-open-evening",
      title: "Volunteer open evening",
      date: "2026-11-05T18:30:00",
      location: "Brightpath office, 12 Riverside Lane",
      summary: "Meet the team, hear about our projects and find the volunteering role that fits you.",
      body: [
        "An informal evening for anyone curious about volunteering. No commitment needed.",
        "Refreshments provided. Please let us know you are coming through the contact form.",
      ],
      image: "",
      ctaLabel: "Tell us you’re coming",
      ctaHref: "/get-involved",
    },
    {
      slug: "winter-gala-2026",
      title: "Winter gala dinner",
      date: "2026-12-12T19:00:00",
      location: "The Grand Hall, Springfield",
      summary: "An evening of dinner, music and stories from the villages we work with.",
      body: ["Our biggest fundraiser of the year, with a silent auction and live music."],
      image: "",
    },
    {
      slug: "school-opening-2026",
      title: "New school opening in Kiwanja",
      date: "2026-03-14T10:00:00",
      location: "Kiwanja village",
      summary: "Celebrating the opening of a six-classroom school built with the community.",
      body: ["Thank you to every supporter who made the Kiwanja school possible."],
      image: "",
    },
  ],

  blog: [
    {
      slug: "one-well-many-futures",
      title: "One well, many futures",
      date: "2026-09-02",
      author: "Priya Nair",
      excerpt: "How a single well in Mato village changed school attendance for girls.",
      body: [
        "Before the well, girls in Mato walked three hours a day to fetch water. Most missed school at least twice a week.",
        "Eighteen months later, attendance among girls has risen by a third, and the village water committee has saved enough to fund its own repairs.",
        "Stories like this are why we measure success by what continues after we leave.",
      ],
      image: "",
      tags: ["Clean water", "Education"],
    },
    {
      slug: "meet-our-health-workers",
      title: "Meet our community health workers",
      date: "2026-07-21",
      author: "Daniel Reyes",
      excerpt: "Twelve newly trained health workers are now serving 9,000 people.",
      body: [
        "This summer twelve health workers completed their six-month training programme.",
        "Each now serves around 750 neighbours, treating common illness and supporting new mothers.",
      ],
      image: "",
      tags: ["Health"],
    },
    {
      slug: "annual-report-2025",
      title: "Our 2025 annual report",
      date: "2026-04-10",
      author: "Amara Okafor",
      excerpt: "Where your money went last year, and what we learned.",
      body: [
        "In 2025 we spent 92 cents of every dollar directly on programmes.",
        "The full audited accounts are available on request.",
      ],
      image: "",
      tags: ["Transparency"],
    },
  ],

  footer: {
    note: "Brightpath Foundation is a registered charity. This site is built from an open NGO website template.",
  },
};

export default siteConfig;
