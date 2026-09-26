import { promises as fs } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import type { SubmissionInput } from "./validation";

/**
 * A tiny file-backed store for form submissions.
 *
 * It keeps the template dependency-free and works anywhere with a writable
 * disk (a VPS, Docker, `npm start`). For serverless hosts with a read-only
 * filesystem, swap the two functions below for a database call; nothing else
 * in the app needs to change.
 */
type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never;

export type StoredSubmission = DistributiveOmit<SubmissionInput, "website" | "consent"> & {
  id: string;
  createdAt: string;
  ip?: string;
  status: "new" | "read";
};

function storePath() {
  const configured = process.env.SUBMISSIONS_FILE;
  return configured
    ? path.resolve(/* turbopackIgnore: true */ configured)
    : path.join(process.cwd(), "data", "submissions.json");
}

// Serialise writes within this process so concurrent requests can't clobber each other.
let queue: Promise<unknown> = Promise.resolve();
function serialised<T>(fn: () => Promise<T>): Promise<T> {
  const next = queue.then(fn, fn);
  queue = next.catch(() => undefined);
  return next;
}

async function readAll(file: string): Promise<StoredSubmission[]> {
  try {
    return JSON.parse(await fs.readFile(file, "utf8")) as StoredSubmission[];
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw err;
  }
}

export async function listSubmissions(): Promise<StoredSubmission[]> {
  const all = await readAll(storePath());
  return all.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export function saveSubmission(input: SubmissionInput, meta: { ip?: string } = {}): Promise<StoredSubmission> {
  return serialised(async () => {
    const file = storePath();
    const { website: _hp, consent: _c, ...fields } = input;
    const record: StoredSubmission = {
      ...fields,
      id: randomUUID(),
      createdAt: new Date().toISOString(),
      ip: meta.ip,
      status: "new",
    };
    const all = await readAll(file);
    all.push(record);
    await fs.mkdir(path.dirname(file), { recursive: true });
    // Write to a temp file then rename, so a crash never leaves half-written JSON.
    const tmp = `${file}.${process.pid}.tmp`;
    await fs.writeFile(tmp, JSON.stringify(all, null, 2));
    await fs.rename(tmp, file);
    return record;
  });
}
