import type { Metadata } from "next";
import { getEvents } from "@/lib/content";
import { PageHeader } from "@/components/PageHeader";
import { EventCard } from "@/components/Cards";

export const metadata: Metadata = { title: "Events" };
// Re-evaluate upcoming vs past at most hourly.
export const revalidate = 3600;

export default function EventsPage() {
  const { upcoming, past } = getEvents();
  return (
    <>
      <PageHeader eyebrow="Events" title="Join us" intro="Fundraisers, open evenings and celebrations. Everyone is welcome." />
      <section className="section">
        <div className="container">
          <h2>Upcoming</h2>
          {upcoming.length ? (
            <div className="stack">
              {upcoming.map((e) => (
                <EventCard key={e.slug} event={e} />
              ))}
            </div>
          ) : (
            <p className="muted">No upcoming events right now. Check back soon.</p>
          )}
          {past.length > 0 && (
            <>
              <h2 className="mt-lg">Past events</h2>
              <div className="stack">
                {past.map((e) => (
                  <EventCard key={e.slug} event={e} past />
                ))}
              </div>
            </>
          )}
        </div>
      </section>
    </>
  );
}
