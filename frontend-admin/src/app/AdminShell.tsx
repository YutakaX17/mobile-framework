import { shellMetrics, workQueue } from "./adminShellModel";

const navItems = ["Dashboard", "Apps", "Forms", "Themes", "Workflows", "Deployments"];

export function AdminShell() {
  return (
    <main className="admin-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">
            MF
          </span>
          <span className="brand-name">Mobile Framework</span>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <a className={item === "Dashboard" ? "nav-link active" : "nav-link"} href="/" key={item}>
              {item}
            </a>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Admin dashboard</p>
            <h1>Operational control surface</h1>
          </div>
          <div className="topbar-actions" aria-label="Current workspace controls">
            <button type="button">Validate</button>
            <button type="button" className="primary-action">
              Publish review
            </button>
          </div>
        </header>

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
      </section>
    </main>
  );
}
