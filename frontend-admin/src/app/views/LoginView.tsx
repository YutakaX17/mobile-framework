import { type FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAuthSession } from "../../auth/AuthProvider";
import { getPostLoginPath } from "../../auth/authSession";

export function LoginView() {
  const { signIn, state } = useAuthSession();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(state.user?.email ?? "admin@example.test");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    signIn(email);
    navigate(getPostLoginPath(searchParams.get("returnTo")), { replace: true });
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
          <label htmlFor="admin-email">Email</label>
          <input
            id="admin-email"
            name="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          <button className="primary-action" type="submit">
            Continue
          </button>
        </form>
      </section>
    </main>
  );
}
