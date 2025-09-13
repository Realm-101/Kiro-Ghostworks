import { z } from 'zod';

// Workspace creation request
export const CreateWorkspaceRequest = z.object({
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/),
});
export type CreateWorkspaceRequest = z.infer<typeof CreateWorkspaceRequest>;

// Workspace update request
export const UpdateWorkspaceRequest = z.object({
  name: z.string().min(1).max(255).optional(),
  settings: z.record(z.any()).optional(),
});
export type UpdateWorkspaceRequest = z.infer<typeof UpdateWorkspaceRequest>;