import type { AdminAuthUser } from "../auth/authSession";
import type { NotificationInput } from "../app/notificationModel";
import type { AdminModuleContribution } from "../modules/moduleRegistry";

export function createTestUser(overrides: Partial<AdminAuthUser> = {}): AdminAuthUser {
  return {
    displayName: "Test Admin",
    email: "test-admin@example.test",
    roles: ["platform-admin"],
    ...overrides
  };
}

export function createTestModuleContribution(
  overrides: Partial<AdminModuleContribution> = {}
): AdminModuleContribution {
  return {
    area: "builder",
    capabilities: ["test:manage"],
    icon: "apps",
    id: "test-module",
    label: "Test Module",
    order: 100,
    routePath: "/test-module",
    section: "Test module",
    summary: "Test module workspace",
    ...overrides
  };
}

export function createTestNotification(overrides: Partial<NotificationInput> = {}): NotificationInput {
  return {
    message: "A test notification was created.",
    title: "Test notification",
    tone: "info",
    ...overrides
  };
}
