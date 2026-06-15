import type { AdminRoute } from "../routes";

type PlaceholderViewProps = {
  route: AdminRoute | undefined;
};

export function PlaceholderView({ route }: PlaceholderViewProps) {
  if (!route) {
    return (
      <section className="empty-state" aria-labelledby="not-found-title">
        <p className="eyebrow">Route not found</p>
        <h2 id="not-found-title">No workspace is registered here</h2>
        <p>Use the primary navigation to return to a configured admin area.</p>
      </section>
    );
  }

  return (
    <section className="empty-state" aria-labelledby={`${route.label}-title`}>
      <p className="eyebrow">{route.section}</p>
      <h2 id={`${route.label}-title`}>{route.summary}</h2>
      <p>This workspace is ready for the next implementation task.</p>
    </section>
  );
}
