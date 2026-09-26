import { z } from "zod";
import { site } from "./content";

const roles = site.getInvolved.volunteerRoles as [string, ...string[]];
const availability = site.getInvolved.availabilityOptions as [string, ...string[]];

const base = {
  name: z.string().trim().min(2, "Please enter your name.").max(100, "Name is too long."),
  email: z.string().trim().toLowerCase().pipe(z.email("Please enter a valid email address.")),
  phone: z
    .string()
    .trim()
    .max(30, "Phone number is too long.")
    .regex(/^[+()\d\s.-]*$/, "Phone number can only contain digits, spaces and + ( ) - .")
    .optional()
    .default(""),
  consent: z.literal(true, { error: "Please agree so we can contact you." }),
  /** Honeypot: hidden from people, filled in by bots. Must stay empty. */
  website: z.string().max(0).optional().default(""),
};

export const volunteerSchema = z.object({
  kind: z.literal("volunteer"),
  ...base,
  roles: z.array(z.enum(roles)).min(1, "Pick at least one area you are interested in."),
  availability: z.enum(availability, { error: "Please tell us when you are available." }),
  message: z.string().trim().max(2000, "Message is too long.").optional().default(""),
});

export const contactSchema = z.object({
  kind: z.literal("contact"),
  ...base,
  subject: z.string().trim().min(3, "Please add a subject.").max(150, "Subject is too long."),
  message: z
    .string()
    .trim()
    .min(10, "Please write at least a sentence so we can help.")
    .max(2000, "Message is too long."),
});

export const submissionSchema = z.discriminatedUnion("kind", [volunteerSchema, contactSchema], {
  error: "Unknown form type.",
});

export type SubmissionInput = z.infer<typeof submissionSchema>;
export type FieldErrors = Record<string, string>;

/** Validate untrusted input. Returns either clean data or one message per field. */
export function validateSubmission(
  input: unknown,
): { ok: true; data: SubmissionInput } | { ok: false; errors: FieldErrors } {
  const result = submissionSchema.safeParse(input);
  if (result.success) return { ok: true, data: result.data };
  const errors: FieldErrors = {};
  for (const issue of result.error.issues) {
    const key = issue.path.length ? String(issue.path[0]) : "form";
    errors[key] ??= issue.message;
  }
  return { ok: false, errors };
}

export const mockDonationSchema = z.object({
  amount: z.coerce
    .number({ error: "Please enter an amount." })
    .min(1, "The minimum gift is 1.")
    .max(100000, "For gifts this large please contact us directly."),
  frequency: z.enum(["once", "monthly"]),
  name: base.name,
  email: base.email,
});
