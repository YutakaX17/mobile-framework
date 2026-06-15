import type { IconName } from "../design-system";

export type ShellActionVariant = "primary" | "secondary";

export type ShellAction = {
  icon: IconName;
  id: string;
  label: string;
  variant: ShellActionVariant;
};

export const shellActions: ShellAction[] = [
  {
    icon: "validate",
    id: "validate",
    label: "Validate",
    variant: "secondary"
  },
  {
    icon: "publish",
    id: "publish-review",
    label: "Publish review",
    variant: "primary"
  }
];

export function getShellActionClassName(action: ShellAction): string | undefined {
  return action.variant === "primary" ? "primary-action" : undefined;
}

export function getUserRoleLabel(roles: string[]): string {
  if (roles.length === 0) {
    return "No roles assigned";
  }

  return roles.join(", ");
}
