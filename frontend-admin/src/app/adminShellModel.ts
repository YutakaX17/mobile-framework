export type ShellMetric = {
  label: string;
  value: string;
  tone: "neutral" | "good" | "warning" | "critical";
};

export type WorkQueueItem = {
  id: string;
  area: string;
  title: string;
  status: "ready" | "draft" | "blocked";
  owner: string;
};

export const shellMetrics: ShellMetric[] = [
  { label: "Draft packages", value: "3", tone: "neutral" },
  { label: "Validation errors", value: "1", tone: "critical" },
  { label: "Pending publishes", value: "2", tone: "warning" },
  { label: "Active modules", value: "8", tone: "good" }
];

export const workQueue: WorkQueueItem[] = [
  {
    id: "WF-101",
    area: "Forms",
    title: "Patient intake needs validation rules",
    status: "draft",
    owner: "Builder"
  },
  {
    id: "PKG-014",
    area: "Deployment",
    title: "Field operations package awaiting review",
    status: "ready",
    owner: "Release"
  },
  {
    id: "SYNC-022",
    area: "Sync",
    title: "Manual review queue has one conflict policy gap",
    status: "blocked",
    owner: "Operations"
  }
];

export function countQueueItemsByStatus(status: WorkQueueItem["status"]): number {
  return workQueue.filter((item) => item.status === status).length;
}
