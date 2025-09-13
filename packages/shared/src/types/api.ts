import { z } from 'zod';

// Generic API response wrapper
export const ApiResponse = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: dataSchema,
    success: z.boolean().default(true),
    message: z.string().optional(),
    requestId: z.string().uuid(),
    timestamp: z.string().datetime(),
  });

// Paginated response
export const PaginatedResponse = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number().min(0),
    limit: z.number().min(1),
    offset: z.number().min(0),
    hasMore: z.boolean(),
  });

// Error response
export const ErrorResponse = z.object({
  error: z.string(),
  message: z.string(),
  details: z.record(z.any()).optional(),
  requestId: z.string().uuid(),
  timestamp: z.string().datetime(),
});
export type ErrorResponse = z.infer<typeof ErrorResponse>;

// Validation error details
export const ValidationError = z.object({
  field: z.string(),
  message: z.string(),
  code: z.string(),
});
export type ValidationError = z.infer<typeof ValidationError>;

// Validation error response
export const ValidationErrorResponse = ErrorResponse.extend({
  validationErrors: z.array(ValidationError),
});
export type ValidationErrorResponse = z.infer<typeof ValidationErrorResponse>;

// Health check response
export const HealthResponse = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  version: z.string(),
  timestamp: z.string().datetime(),
  services: z.record(z.object({
    status: z.enum(['up', 'down']),
    responseTime: z.number().optional(),
    error: z.string().optional(),
  })),
});
export type HealthResponse = z.infer<typeof HealthResponse>;