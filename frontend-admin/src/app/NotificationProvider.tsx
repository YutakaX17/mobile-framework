import { createContext, type PropsWithChildren, useContext, useMemo, useReducer, useRef } from "react";

import {
  createNotification,
  initialNotificationState,
  type AdminNotification,
  type NotificationInput,
  notificationReducer
} from "./notificationModel";

type NotificationContextValue = {
  addNotification(input: NotificationInput): void;
  clearNotifications(): void;
  dismissNotification(id: string): void;
  notifications: AdminNotification[];
};

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(notificationReducer, initialNotificationState);
  const nextId = useRef(1);
  const value = useMemo<NotificationContextValue>(
    () => ({
      addNotification(input) {
        dispatch({
          notification: createNotification(`notification-${nextId.current++}`, input),
          type: "add"
        });
      },
      clearNotifications() {
        dispatch({ type: "clear" });
      },
      dismissNotification(id) {
        dispatch({ id, type: "dismiss" });
      },
      notifications: state.notifications
    }),
    [state.notifications]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications(): NotificationContextValue {
  const value = useContext(NotificationContext);

  if (!value) {
    throw new Error("useNotifications must be used inside NotificationProvider.");
  }

  return value;
}

export function NotificationCenter() {
  const { dismissNotification, notifications } = useNotifications();

  return (
    <section aria-label="Notifications" aria-live="polite" className="notification-region">
      {notifications.map((notification) => (
        <article className={`notification notification-${notification.tone}`} key={notification.id}>
          <div>
            <strong>{notification.title}</strong>
            <p>{notification.message}</p>
          </div>
          <button type="button" onClick={() => dismissNotification(notification.id)}>
            Dismiss
          </button>
        </article>
      ))}
    </section>
  );
}
