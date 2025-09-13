// API constants
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    VERIFY_EMAIL: '/api/v1/auth/verify-email',
  },
  WORKSPACES: {
    LIST: '/api/v1/workspaces',
    CREATE: '/api/v1/workspaces',
    GET: (id: string) => `/api/v1/workspaces/${id}`,
    UPDATE: (id: string) => `/api/v1/workspaces/${id}`,
    DELETE: (id: string) => `/api/v1/workspaces/${id}`,
    MEMBERS: (id: string) => `/api/v1/workspaces/${id}/members`,
  },
  ARTIFACTS: {
    LIST: '/api/v1/artifacts',
    CREATE: '/api/v1/artifacts',
    GET: (id: string) => `/api/v1/artifacts/${id}`,
    UPDATE: (id: string) => `/api/v1/artifacts/${id}`,
    DELETE: (id: string) => `/api/v1/artifacts/${id}`,
    SEARCH: '/api/v1/artifacts/search',
  },
  HEALTH: '/api/v1/health',
  METRICS: '/metrics',
} as const;

// Workspace roles
export const WORKSPACE_ROLES = {
  OWNER: 'owner',
  ADMIN: 'admin',
  MEMBER: 'member',
} as const;

// HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// Pagination defaults
export const PAGINATION = {
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100,
  DEFAULT_OFFSET: 0,
} as const;

// JWT token expiration times
export const JWT_EXPIRATION = {
  ACCESS_TOKEN: '15m',
  REFRESH_TOKEN: '7d',
} as const;

// Validation limits
export const VALIDATION_LIMITS = {
  NAME_MAX_LENGTH: 255,
  DESCRIPTION_MAX_LENGTH: 1000,
  SLUG_MAX_LENGTH: 100,
  PASSWORD_MIN_LENGTH: 8,
  TAGS_MAX_COUNT: 20,
  TAG_MAX_LENGTH: 50,
} as const;