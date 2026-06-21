import type { IconName } from "../design-system";

export type AdminModuleArea = "builder" | "core" | "operations";

export type AdminModuleContribution = {
  area: AdminModuleArea;
  capabilities: string[];
  icon: IconName;
  id: string;
  label: string;
  order: number;
  routePath: string;
  section: string;
  summary: string;
};

export type ModuleRegistryValidation = {
  duplicateIds: string[];
  duplicateRoutePaths: string[];
  isValid: boolean;
};

export const adminModuleContributions: AdminModuleContribution[] = [
  {
    area: "core",
    capabilities: ["dashboard:view"],
    icon: "dashboard",
    id: "dashboard",
    label: "Dashboard",
    order: 10,
    routePath: "/dashboard",
    section: "Admin dashboard",
    summary: "Operational control surface"
  },
  {
    area: "core",
    capabilities: ["apps:manage", "forms:manage", "themes:manage", "deployments:manage"],
    icon: "setup",
    id: "setup",
    label: "Setup",
    order: 15,
    routePath: "/setup",
    section: "MVP setup",
    summary: "Guided Field Ops launch"
  },
  {
    area: "builder",
    capabilities: ["apps:manage"],
    icon: "apps",
    id: "apps",
    label: "Apps",
    order: 20,
    routePath: "/apps",
    section: "App builder",
    summary: "App composition workspace"
  },
  {
    area: "builder",
    capabilities: ["forms:manage"],
    icon: "forms",
    id: "forms",
    label: "Forms",
    order: 30,
    routePath: "/forms",
    section: "Form builder",
    summary: "Form definition workspace"
  },
  {
    area: "builder",
    capabilities: ["themes:manage"],
    icon: "themes",
    id: "themes",
    label: "Themes",
    order: 40,
    routePath: "/themes",
    section: "Theme builder",
    summary: "Design token workspace"
  },
  {
    area: "operations",
    capabilities: ["workflows:manage"],
    icon: "workflows",
    id: "workflows",
    label: "Workflows",
    order: 50,
    routePath: "/workflows",
    section: "Workflow builder",
    summary: "Approval and automation workspace"
  },
  {
    area: "operations",
    capabilities: ["apps:manage"],
    icon: "modules",
    id: "modules",
    label: "Modules",
    order: 55,
    routePath: "/modules",
    section: "Plugin status",
    summary: "Installed module compatibility"
  },
  {
    area: "operations",
    capabilities: ["deployments:manage"],
    icon: "deployments",
    id: "deployments",
    label: "Deployments",
    order: 60,
    routePath: "/deployments",
    section: "Deployment manager",
    summary: "Package release workspace"
  }
];

export function getOrderedAdminModules(
  contributions: AdminModuleContribution[] = adminModuleContributions
): AdminModuleContribution[] {
  return [...contributions].sort((left, right) => left.order - right.order || left.label.localeCompare(right.label));
}

export function findAdminModuleByRoute(
  routePath: string,
  contributions: AdminModuleContribution[] = adminModuleContributions
): AdminModuleContribution | undefined {
  return contributions.find((contribution) => contribution.routePath === routePath);
}

export function validateAdminModuleRegistry(
  contributions: AdminModuleContribution[] = adminModuleContributions
): ModuleRegistryValidation {
  const duplicateIds = findDuplicates(contributions.map((contribution) => contribution.id));
  const duplicateRoutePaths = findDuplicates(contributions.map((contribution) => contribution.routePath));

  return {
    duplicateIds,
    duplicateRoutePaths,
    isValid: duplicateIds.length === 0 && duplicateRoutePaths.length === 0
  };
}

export function registerAdminModule(
  contributions: AdminModuleContribution[],
  contribution: AdminModuleContribution
): AdminModuleContribution[] {
  const nextContributions = [...contributions, contribution];
  const validation = validateAdminModuleRegistry(nextContributions);

  if (!validation.isValid) {
    throw new Error("Admin module registry contains duplicate ids or route paths.");
  }

  return getOrderedAdminModules(nextContributions);
}

function findDuplicates(values: string[]): string[] {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }

  return [...duplicates].sort();
}
