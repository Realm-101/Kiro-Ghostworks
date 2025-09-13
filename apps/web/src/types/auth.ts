import { z } from 'zod';

// User schema
export const User = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  isVerified: z.boolean(),
  createdAt: z.string().datetime(),
});
export type User = z.infer<typeof User>;

// Tenant/Workspace schema
export const Tenant = z.object({
  id: z.string().uuid(),
  name: z.string(),
  slug: z.string(),
  createdAt: z.string().datetime(),
  settings: z.record(z.any()).default({}),
});
export type Tenant = z.infer<typeof Tenant>;

// Workspace membership schema
export const WorkspaceMembership = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  tenantId: z.string().uuid(),
  role: z.enum(['owner', 'admin', 'member']),
  createdAt: z.string().datetime(),
  tenant: Tenant,
});
export type WorkspaceMembership = z.infer<typeof WorkspaceMembership>;

// Auth tokens
export const AuthTokens = z.object({
  accessToken: z.string(),
  refreshToken: z.string(),
  expiresIn: z.number(),
});
export type AuthTokens = z.infer<typeof AuthTokens>;

// Login request
export const LoginRequest = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});
export type LoginRequest = z.infer<typeof LoginRequest>;

// Register request
export const RegisterRequest = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      'Password must contain at least one uppercase letter, one lowercase letter, and one number'
    ),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});
export type RegisterRequest = z.infer<typeof RegisterRequest>;

// Auth response
export const AuthResponse = z.object({
  user: User,
  tokens: AuthTokens,
  workspaces: z.array(WorkspaceMembership),
});
export type AuthResponse = z.infer<typeof AuthResponse>;

// Current user context
export const AuthUser = z.object({
  user: User,
  currentWorkspace: WorkspaceMembership.nullable(),
  workspaces: z.array(WorkspaceMembership),
});
export type AuthUser = z.infer<typeof AuthUser>;

// Workspace switch request
export const WorkspaceSwitchRequest = z.object({
  workspaceId: z.string().uuid(),
});
export type WorkspaceSwitchRequest = z.infer<typeof WorkspaceSwitchRequest>;