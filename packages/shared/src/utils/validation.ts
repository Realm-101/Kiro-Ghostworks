import { z } from 'zod';

/**
 * Validates UUID format
 */
export const isValidUUID = (value: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(value);
};

/**
 * Validates email format
 */
export const isValidEmail = (email: string): boolean => {
  return z.string().email().safeParse(email).success;
};

/**
 * Validates workspace slug format
 */
export const isValidSlug = (slug: string): boolean => {
  const slugRegex = /^[a-z0-9-]+$/;
  return slugRegex.test(slug) && slug.length >= 1 && slug.length <= 100;
};

/**
 * Validates password strength
 */
export const isValidPassword = (password: string): boolean => {
  // At least 8 characters, contains uppercase, lowercase, number
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
};

/**
 * Sanitizes string input to prevent XSS
 */
export const sanitizeString = (input: string): string => {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .trim();
};

/**
 * Validates and parses JSON safely
 */
export const safeJsonParse = <T = any>(jsonString: string): T | null => {
  try {
    return JSON.parse(jsonString);
  } catch {
    return null;
  }
};