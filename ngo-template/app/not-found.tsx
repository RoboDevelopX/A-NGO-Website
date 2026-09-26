import Link from "next/link";

export default function NotFound() {
  return (
    <section className="section">
      <div className="container container--narrow center">
        <h1>Page not found</h1>
        <p className="lead">Sorry, we couldn't find that page.</p>
        <Link href="/" className="btn btn--primary">
          Back to home
        </Link>
      </div>
    </section>
  );
}
