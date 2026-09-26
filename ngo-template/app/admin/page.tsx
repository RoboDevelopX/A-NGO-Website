import type { Metadata } from "next";
import { AdminSubmissions } from "@/components/AdminSubmissions";

export const metadata: Metadata = { title: "Submissions", robots: { index: false, follow: false } };

export default function AdminPage() {
  return (
    <section className="section">
      <div className="container">
        <h1>Form submissions</h1>
        <p className="muted">Staff only. Enter the ADMIN_TOKEN configured on the server.</p>
        <AdminSubmissions />
      </div>
    </section>
  );
}
