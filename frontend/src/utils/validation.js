import { z } from 'zod';

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