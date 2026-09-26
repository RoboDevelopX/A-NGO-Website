import { NextResponse } from "next/server";
import { randomBytes } from "node:crypto";
import { mockDonationSchema } from "@/lib/validation";

export const runtime = "nodejs";

/**
 * MOCK payment endpoint. No money moves and no card data is accepted or stored.
 * Replace this handler with a real provider (Stripe Checkout, PayPal, Razorpay…)
 * when the organisation is ready to take payments.
 */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid request body." }, { status: 400 });
  }
  const result = mockDonationSchema.safeParse(body);
  if (!result.success) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of result.error.issues) fieldErrors[String(issue.path[0] ?? "form")] ??= issue.message;
    return NextResponse.json({ ok: false, error: "Please check the form.", fieldErrors }, { status: 422 });
  }
  // Simulate provider latency so the UI's processing state is visible.
  await new Promise((r) => setTimeout(r, 600));
  return NextResponse.json({
    ok: true,
    mock: true,
    receiptId: `MOCK-${randomBytes(4).toString("hex").toUpperCase()}`,
    amount: result.data.amount,
    frequency: result.data.frequency,
  });
}
