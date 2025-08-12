import { z } from "zod";

// Common schemas you can expand later
export const EmailSchema = z.string().email();
export const PhoneSchema = z.string().trim().min(7).regex(/^\+?[0-9()\-\s]+$/);

export const PlanSchema = z.object({
  id: z.string().uuid().optional(),
  name: z.string().trim().min(1, "Plan name is required"),
  price: z.number().nonnegative(),
  cycleDays: z.number().int().positive(),
  description: z.string().optional().default(""),
  active: z.boolean().optional().default(true),
});

// Legacy schemas (keeping for backward compatibility)
export const ClientSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  phone: z.string().optional().or(z.literal('')),
  membershipType: z.string().min(1),
  amount: z.number().nonnegative('Amount must be >= 0'),
  joinDate: z.string().optional(),
  lastPayment: z.string().optional().nullable(),
  nextDue: z.string().min(1),
  status: z.enum(['Active', 'Overdue']).optional(),
  overdue: z.number().int().min(0).optional(),
});

export const PaymentSchema = z.object({
  clientId: z.string().min(1),
  date: z.string().min(1),
  amount: z.number().positive('Payment must be > 0'),
  monthsCovered: z.number().int().min(1),
  method: z.string().min(1),
});

// Small helpers (optional)
export function assertEmail(email) { return EmailSchema.parse(email); }
export function assertPhone(phone) { return PhoneSchema.parse(phone); }
export function assertPlan(plan) {
  const parsed = PlanSchema.safeParse(plan);
  if (!parsed.success) throw new Error(parsed.error.issues?.[0]?.message || "Invalid plan");
  return parsed.data;
}

// Re-export z for any callers that use `z` directly
export { z };