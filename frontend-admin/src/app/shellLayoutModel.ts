import type { IconName } from "../design-system";
import type { NotificationInput } from "./notificationModel";

export type ShellActionVariant = "primary" | "secondary";

export type ShellAction = {
  icon: IconName;
  id: string;
  label: string;
  notification: NotificationInput;
  variant: ShellActionVariant;
};

export const shellActions: ShellAction[] = [
  {
    icon: "validate",
    id: "validate",
    label: "Validate",
    notification: {
      message: "The current workspace has been queued for local validation.",
      title: "Validation queued",
      tone: "success"
    },
    variant: "secondary"
  },
  {
    icon: "publish",
    id: "publish-review",
    label: "Publish review",
    notification: {
      message: "A publish review summary will be prepared when deployment workflows are connected.",
      title: "Publish review pending",
      tone: "info"
    },
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
