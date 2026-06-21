import { type FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAuthSession } from "../../auth/AuthProvider";
import { getPostLoginPath } from "../../auth/authSession";
import { AdminIcon } from "../../design-system";

export function LoginView() {
  const { signIn, state } = useAuthSession();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [password, setPassword] = useState("demo-admin-password");
  const [username, setUsername] = useState(state.user?.username ?? "demo-admin");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await signIn(username, password);
      navigate(getPostLoginPath(searchParams.get("returnTo")), { replace: true });
    } catch {
      setError("Sign in failed. Check your username and password.");
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="brand-block login-brand">
          <span className="brand-mark" aria-hidden="true">
            MF
          </span>
          <span className="brand-name">Mobile Framework</span>
        </div>
        <p className="eyebrow">Admin access</p>
        <h1 id="login-title">Sign in to continue</h1>
        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="admin-username">Username</label>
          <input
            autoComplete="username"
            id="admin-username"
            name="username"
            onChange={(event) => setUsername(event.target.value)}
            required
            type="text"
            value={username}
          />
          <label htmlFor="admin-password">Password</label>
          <input
            autoComplete="current-password"
            id="admin-password"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          {error || state.status === "error" ? <p className="form-error">{error || state.error}</p> : null}
          <button className="primary-action" type="submit">
            <AdminIcon name="login" />
            {state.status === "loading" ? "Signing in" : "Continue"}
          </button>
        </form>
      </section>
    </main>
  );
}
