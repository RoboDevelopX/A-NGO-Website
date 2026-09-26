import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { POST as contactPost } from "@/app/api/contact/route";
import { GET as submissionsGet } from "@/app/api/submissions/route";
import { POST as donatePost } from "@/app/api/donate/route";
import { resetRateLimit } from "@/lib/rateLimit";

let dir: string;
let file: string;

const volunteer = {
  kind: "volunteer",
  name: "Sam Lee",
  email: "Sam@Example.org",
  roles: ["Event support"],
  availability: "Weekends",
  consent: true,
};
const contact = {
  kind: "contact",
  name: "Jo Park",
  email: "jo@example.org",
  subject: "Partnership",
  message: "We'd love to talk about a school partnership.",
  consent: true,
};

function post(body: unknown, ip = "1.2.3.4") {
  return contactPost(
    new Request("http://localhost/api/contact", {
      method: "POST",
      headers: { "content-type": "application/json", "x-forwarded-for": ip },
      body: typeof body === "string" ? body : JSON.stringify(body),
    }),
  );
}

beforeEach(() => {
  dir = mkdtempSync(path.join(tmpdir(), "ngo-"));
  file = path.join(dir, "submissions.json");
  process.env.SUBMISSIONS_FILE = file;
  process.env.ADMIN_TOKEN = "secret";
  resetRateLimit();
});
afterEach(() => rmSync(dir, { recursive: true, force: true }));

describe("POST /api/contact", () => {
  it("stores a valid volunteer application", async () => {
    const res = await post(volunteer);
    expect(res.status).toBe(201);
    const saved = JSON.parse(readFileSync(file, "utf8"));
    expect(saved).toHaveLength(1);
    expect(saved[0]).toMatchObject({ kind: "volunteer", email: "sam@example.org", roles: ["Event support"] });
    expect(saved[0]).not.toHaveProperty("consent");
  });

  it("stores a valid contact message", async () => {
    expect((await post(contact)).status).toBe(201);
    expect(JSON.parse(readFileSync(file, "utf8"))[0].subject).toBe("Partnership");
  });

  it("returns field errors for invalid input and stores nothing", async () => {
    const res = await post({ kind: "volunteer", name: "", email: "nope", roles: ["Hacking"], consent: false });
    expect(res.status).toBe(422);
    const data = await res.json();
    expect(Object.keys(data.fieldErrors)).toEqual(
      expect.arrayContaining(["name", "email", "roles", "availability", "consent"]),
    );
    expect(existsSync(file)).toBe(false);
  });

  it("requires a message for general enquiries", async () => {
    const res = await post({ ...contact, message: "hi" });
    expect(res.status).toBe(422);
    expect((await res.json()).fieldErrors.message).toBeDefined();
  });

  it("rejects malformed JSON", async () => {
    expect((await post("{not json")).status).toBe(400);
  });

  it("silently drops honeypot submissions", async () => {
    const res = await post({ ...contact, website: "http://spam.example" });
    expect(res.status).toBe(201);
    expect(existsSync(file)).toBe(false);
  });

  it("rate-limits repeated submissions from one IP", async () => {
    for (let i = 0; i < 5; i++) expect((await post(contact, "9.9.9.9")).status).toBe(201);
    const res = await post(contact, "9.9.9.9");
    expect(res.status).toBe(429);
    expect(res.headers.get("retry-after")).toBeTruthy();
    expect((await post(contact, "8.8.8.8")).status).toBe(201);
  });

  it("keeps every record when requests arrive concurrently", async () => {
    await Promise.all(Array.from({ length: 5 }, (_, i) => post(contact, `10.0.0.${i}`)));
    expect(JSON.parse(readFileSync(file, "utf8"))).toHaveLength(5);
  });
});

describe("GET /api/submissions", () => {
  const get = (token?: string) =>
    submissionsGet(
      new Request("http://localhost/api/submissions", {
        headers: token ? { authorization: `Bearer ${token}` } : {},
      }),
    );

  it("rejects missing or wrong tokens", async () => {
    expect((await get()).status).toBe(401);
    expect((await get("wrong")).status).toBe(401);
  });

  it("lists submissions newest first for admins", async () => {
    await post(volunteer);
    await post(contact);
    const data = await (await get("secret")).json();
    expect(data.submissions.map((s: { kind: string }) => s.kind)).toEqual(["contact", "volunteer"]);
  });

  it("is disabled when ADMIN_TOKEN is unset", async () => {
    delete process.env.ADMIN_TOKEN;
    expect((await get("secret")).status).toBe(503);
  });
});

describe("POST /api/donate (mock)", () => {
  const donate = (body: unknown) =>
    donatePost(new Request("http://localhost/api/donate", { method: "POST", body: JSON.stringify(body) }));

  it("returns a mock receipt without taking payment", async () => {
    const data = await (await donate({ amount: 50, frequency: "once", name: "Ana", email: "ana@example.org" })).json();
    expect(data).toMatchObject({ ok: true, mock: true, amount: 50 });
    expect(data.receiptId).toMatch(/^MOCK-/);
  });

  it("validates the amount", async () => {
    expect((await donate({ amount: 0, frequency: "once", name: "Ana", email: "ana@example.org" })).status).toBe(422);
  });
});
