/**
 * lib/constants.ts
 * ==================
 * Shared constants kept in sync with backend/dataset/generate_dataset.py
 * (DEPARTMENTS dict) so registration forms and filters offer the same
 * options the seeded dataset actually uses.
 */

export const DEPARTMENTS = [
  "Computer Science",
  "Electronics",
  "Mechanical",
  "Civil",
  "Electrical",
  "Information Technology",
] as const;

export const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8] as const;

export const DESIGNATIONS = ["Assistant Professor", "Associate Professor", "Professor"] as const;

export const GENDERS = ["Male", "Female"] as const;
