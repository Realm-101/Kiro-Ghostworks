import { z } from 'zod';

// Artifact entity
export const Artifact = z.object({
  id: z.string().uuid(),
  tenantId: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string().nullable(),
  tags: z.array(z.string()).default([]),
  metadata: z.record(z.any()).default({}),
  createdBy: z.string().uuid(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});
export type Artifact = z.infer<typeof Artifact>;

// Artifact creation request
export const CreateArtifactRequest = z.object({
  name: z.string().min(1).max(255),
  description: z.string().nullable().optional(),
  tags: z.array(z.string()).default([]),
  metadata: z.record(z.any()).default({}),
});
export type CreateArtifactRequest = z.infer<typeof CreateArtifactRequest>;

// Artifact update request
export const UpdateArtifactRequest = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().nullable().optional(),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.any()).optional(),
});
export type UpdateArtifactRequest = z.infer<typeof UpdateArtifactRequest>;

// Artifact search query
export const ArtifactSearchQuery = z.object({
  q: z.string().optional(), // Full-text search
  tags: z.array(z.string()).default([]), // Tag filtering
  createdAfter: z.string().datetime().optional(),
  createdBefore: z.string().datetime().optional(),
  limit: z.number().min(1).max(100).default(20),
  offset: z.number().min(0).default(0),
});
export type ArtifactSearchQuery = z.infer<typeof ArtifactSearchQuery>;