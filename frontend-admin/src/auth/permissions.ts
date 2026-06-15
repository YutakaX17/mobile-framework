import type { AdminModuleContribution } from "../modules/moduleRegistry";
import type { AdminAuthUser } from "./authSession";

export type Capability = string;
export type Role = string;

export const roleCapabilities: Record<Role, Capability[]> = {
  builder: ["apps:manage", "forms:manage", "themes:manage"],
  operator: ["dashboard:view", "deployments:manage", "workflows:manage"],
  "platform-admin": ["*"]
};

export function getCapabilitiesForRoles(roles: Role[]): Capability[] {
  return [...new Set(roles.flatMap((role) => roleCapabilities[role] ?? []))].sort();
}

export function hasCapability(user: AdminAuthUser | undefined, capability: Capability): boolean {
  if (!user) {
    return false;
  }

  const capabilities = getCapabilitiesForRoles(user.roles);
  return capabilities.includes("*") || capabilities.includes(capability);
}

export function canAccessModule(user: AdminAuthUser | undefined, module: AdminModuleContribution): boolean {
  return module.capabilities.every((capability) => hasCapability(user, capability));
}
