import { shellMetrics, workQueue } from "../adminShellModel";

export function DashboardView() {
  return (
    <>
      <section className="metrics-grid" aria-label="Platform summary">
        {shellMetrics.map((metric) => (
          <article className={`metric metric-${metric.tone}`} key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="work-surface" aria-labelledby="queue-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Builder queue</p>
            <h2 id="queue-title">Items needing attention</h2>
          </div>
          <span className="queue-count">{workQueue.length} open</span>
        </div>

        <div className="queue-table" role="table" aria-label="Builder queue">
          <div className="queue-row queue-head" role="row">
            <span role="columnheader">ID</span>
            <span role="columnheader">Area</span>
            <span role="columnheader">Item</span>
            <span role="columnheader">Status</span>
            <span role="columnheader">Owner</span>
          </div>
          {workQueue.map((item) => (
            <div className="queue-row" role="row" key={item.id}>
              <span role="cell">{item.id}</span>
              <span role="cell">{item.area}</span>
              <span role="cell">{item.title}</span>
              <span role="cell">
                <span className={`status status-${item.status}`}>{item.status}</span>
              </span>
              <span role="cell">{item.owner}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
