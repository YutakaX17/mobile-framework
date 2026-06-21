import { adminApiClient, type AdminApiClient } from "./adminApiClient";

export type ModuleCompatibility = {
  is_compatible: boolean;
  message: string;
  platform_version: string;
};

export type ModuleStatus = {
  compatibility: ModuleCompatibility;
  module_id: string;
  name: string;
  plugin_api_version: number;
  runtime_max_version?: string;
  runtime_min_version?: string;
  status: string;
  templates?: {
    apps?: unknown[];
    forms?: unknown[];
  };
  version: string;
};

export type DeploymentPackageSummary = {
  app_id: string;
  app_version: string;
  channel: string;
  created_at: string;
  form_count?: number;
  hash: string;
  module_count?: number;
  package_id: string;
  platform_version: string;
  runtime_compatibility?: {
    max_version: string;
    min_version: string;
  };
  runtime_max_version: string;
  runtime_min_version: string;
  signature: string;
  signature_status?: "missing" | "present";
  status: string;
  updated_at: string;
};

export type DeploymentPackageDetail = DeploymentPackageSummary & {
  payload?: {
    modules?: Array<{ module_id?: string; version?: string }>;
  };
};

export type CompilePackageRequest = {
  app_id: string;
  channel: string;
  form_ids: string[];
  package_id: string;
  platform_version?: string;
  runtime_max_version?: string;
  runtime_min_version?: string;
  signing_key?: string;
  theme_id: string;
};

type ModuleListResponse = {
  modules: ModuleStatus[];
};

type ModuleDetailResponse = {
  module: ModuleStatus;
};

type PackageListResponse = {
  packages: DeploymentPackageSummary[];
};

type PackageResponse = {
  package: DeploymentPackageDetail;
};

type ManifestResponse = {
  manifest: DeploymentPackageSummary;
};

export async function fetchModuleStatuses(
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<ModuleStatus[]> {
  const result = await client.get<ModuleListResponse>("/modules/", { query: { tenant } });

  if (!result.data || !Array.isArray(result.data.modules)) {
    throw new Error("Module list response did not include a modules array.");
  }

  return result.data.modules;
}

export async function fetchModuleStatus(
  moduleId: string,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<ModuleStatus> {
  const result = await client.get<ModuleDetailResponse>(`/modules/${encodeURIComponent(moduleId)}/`, {
    query: { tenant }
  });

  if (!result.data || !isRecord(result.data.module)) {
    throw new Error("Module detail response did not include a module object.");
  }

  return result.data.module;
}

export async function fetchDeploymentPackages(
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<DeploymentPackageSummary[]> {
  const result = await client.get<PackageListResponse>("/deployment-packages/", { query: { tenant } });

  if (!result.data || !Array.isArray(result.data.packages)) {
    throw new Error("Deployment package response did not include a packages array.");
  }

  return result.data.packages;
}

export async function compileDeploymentPackage(
  request: CompilePackageRequest,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<DeploymentPackageDetail> {
  const result = await client.post<PackageResponse, CompilePackageRequest>("/deployment-packages/compile/", request, {
    query: { tenant }
  });

  if (!result.data || !isRecord(result.data.package)) {
    throw new Error("Package compile response did not include a package object.");
  }

  return result.data.package;
}

export async function activateDeploymentPackage(
  packageId: string,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<DeploymentPackageDetail> {
  const result = await client.post<PackageResponse, Record<string, never>>(
    `/deployment-packages/${encodeURIComponent(packageId)}/activate/`,
    {},
    { query: { tenant } }
  );

  if (!result.data || !isRecord(result.data.package)) {
    throw new Error("Package activation response did not include a package object.");
  }

  return result.data.package;
}

export async function fetchActiveManifest(
  appId: string,
  client: AdminApiClient = adminApiClient,
  tenant = "demo",
  channel = "dev"
): Promise<DeploymentPackageSummary | undefined> {
  try {
    const result = await client.get<ManifestResponse>("/mobile/packages/manifest/", {
      query: { app_id: appId, channel, tenant }
    });

    if (!result.data || !isRecord(result.data.manifest)) {
      throw new Error("Active manifest response did not include a manifest object.");
    }

    return result.data.manifest;
  } catch (error) {
    if (isNotFoundError(error)) {
      return undefined;
    }
    throw error;
  }
}

export function activePackage(packages: DeploymentPackageSummary[]): DeploymentPackageSummary | undefined {
  return packages.find((item) => item.status === "active");
}

export function moduleCompatibilityCount(modules: ModuleStatus[]): number {
  return modules.filter((module) => module.compatibility.is_compatible).length;
}

export function nextPatchVersion(version: string): string {
  const parts = version.split(".").map((part) => Number.parseInt(part, 10));
  if (parts.length < 3 || parts.some((part) => Number.isNaN(part))) {
    return "0.1.1";
  }
  return `${parts[0]}.${parts[1]}.${parts[2] + 1}`;
}

export function packageIdFor(appId: string, version: string): string {
  return `pkg_${appId}_${version.replace(/[^a-zA-Z0-9]+/g, "_")}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNotFoundError(error: unknown): boolean {
  return isRecord(error) && error.status === 404;
}
