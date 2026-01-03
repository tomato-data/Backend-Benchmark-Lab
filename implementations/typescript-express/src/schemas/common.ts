import { z } from "zod";

// Health
export const HealthResponseSchema = z.object({
  status: z.string(),
  server: z.string(),
});
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

// Echo
export const EchoRequestSchema = z.object({
  message: z.string(),
  data: z.record(z.string(), z.any()).nullable().optional(),
});
export type EchoRequest = z.infer<typeof EchoRequestSchema>;

export const EchoResponseSchema = z.object({
  message: z.string(),
  data: z.record(z.string(), z.any()).nullable().optional(),
});
export type EchoResponse = z.infer<typeof EchoResponseSchema>;

// External
export const ExternalResponseSchema = z.object({
  source: z.string(),
  latency_ms: z.number(),
  data: z.record(z.string(), z.any()).nullable().optional(),
});
export type ExternalResponse = z.infer<typeof ExternalResponseSchema>;

// Protected
export const ProtectedResponseSchema = z.object({
  message: z.string(),
  user: z.string().nullable().optional(),
});
export type ProtectedResponse = z.infer<typeof ProtectedResponseSchema>;

// Upload
export const UploadResponseSchema = z.object({
  filename: z.string(),
  size: z.number(),
  content_type: z.string().nullable().optional(),
});
export type UploadResponse = z.infer<typeof UploadResponseSchema>;
