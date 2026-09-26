import { NextResponse } from "next/server";
import { isAdmin } from "@/lib/auth";
import { listSubmissions } from "@/lib/submissions";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** Staff-only list of form submissions. Requires ADMIN_TOKEN. */
export async function GET(request: Request) {
  if (!process.env.ADMIN_TOKEN) {
    return NextResponse.json({ ok: false, error: "Admin access is not configured (set ADMIN_TOKEN)." }, { status: 503 });
  }
  if (!isAdmin(request)) {
    return NextResponse.json({ ok: false, error: "Unauthorized." }, { status: 401 });
  }
  return NextResponse.json({ ok: true, submissions: await listSubmissions() });
}
