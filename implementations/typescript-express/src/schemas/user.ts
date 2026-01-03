import { z } from "zod";

export const UserCreateSchema = z.object({
  name: z.string(),
  email: z.string(),
});
export type UserCreate = z.infer<typeof UserCreateSchema>;

export const UserResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string(),
  createdAt: z.date(),
});
export type UserResponse = z.infer<typeof UserResponseSchema>;
