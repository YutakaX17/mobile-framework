export type NotificationTone = "critical" | "info" | "success" | "warning";

export type AdminNotification = {
  id: string;
  message: string;
  title: string;
  tone: NotificationTone;
};

export type NotificationInput = Omit<AdminNotification, "id">;

export type NotificationAction =
  | {
      notification: AdminNotification;
      type: "add";
    }
  | {
      id: string;
      type: "dismiss";
    }
  | {
      type: "clear";
    };

export type NotificationState = {
  notifications: AdminNotification[];
};

export const initialNotificationState: NotificationState = {
  notifications: []
};

export function notificationReducer(
  state: NotificationState,
  action: NotificationAction
): NotificationState {
  switch (action.type) {
    case "add":
      return {
        notifications: [action.notification, ...state.notifications].slice(0, 4)
      };
    case "dismiss":
      return {
        notifications: state.notifications.filter((notification) => notification.id !== action.id)
      };
    case "clear":
      return initialNotificationState;
    default:
      return state;
  }
}

export function createNotification(id: string, input: NotificationInput): AdminNotification {
  return {
    id,
    ...input
  };
}
