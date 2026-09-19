export type HarnessSnapshot = {
  id: string;
  version: string;
  display_name: string;
  manifest_sha256: string;
  source_sha256: string;
  config_sha256: string;
  source_revision: string;
  image_digest: string;
  description?: string;
  public?: boolean;
  compatible?: boolean;
};

export const DEFAULT_HARNESS_ID = "classic-slide";
