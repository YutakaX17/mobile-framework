import { describe, expect, it } from "vitest";

import {
  createNotification,
  initialNotificationState,
  notificationReducer,
  type NotificationInput
} from "./notificationModel";
import { createTestNotification } from "../tests/testFixtures";

const notification: NotificationInput = createTestNotification({
  message: "The current workspace was queued for validation.",
  title: "Validation queued",
  tone: "success"
});

describe("notification model", () => {
  it("adds notifications newest first", () => {
    const first = createNotification("first", notification);
    const second = createNotification("second", { ...notification, title: "Publish queued" });

    const state = notificationReducer(initialNotificationState, { notification: first, type: "add" });
    const nextState = notificationReducer(state, { notification: second, type: "add" });

    expect(nextState.notifications.map((item) => item.id)).toEqual(["second", "first"]);
  });

  it("keeps the notification list bounded", () => {
    const state = ["1", "2", "3", "4", "5"].reduce(
      (currentState, id) =>
        notificationReducer(currentState, {
          notification: createNotification(id, notification),
          type: "add"
        }),
      initialNotificationState
    );

    expect(state.notifications.map((item) => item.id)).toEqual(["5", "4", "3", "2"]);
  });

  it("dismisses and clears notifications", () => {
    const state = notificationReducer(initialNotificationState, {
      notification: createNotification("first", notification),
      type: "add"
    });

    expect(notificationReducer(state, { id: "first", type: "dismiss" })).toEqual(initialNotificationState);
    expect(notificationReducer(state, { type: "clear" })).toEqual(initialNotificationState);
  });
});
