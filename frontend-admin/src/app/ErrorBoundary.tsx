import { Component, type ErrorInfo, type ReactNode } from "react";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  error: unknown;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    error: undefined
  };

  static getDerivedStateFromError(error: unknown): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: unknown, errorInfo: ErrorInfo) {
    console.error("Admin frontend error boundary caught an error.", error, errorInfo);
  }

  render() {
    if (this.state.error) {
      return <ErrorFallback error={this.state.error} onReset={() => this.setState({ error: undefined })} />;
    }

    return this.props.children;
  }
}

type ErrorFallbackProps = {
  error: unknown;
  onReset(): void;
};

export function ErrorFallback({ error, onReset }: ErrorFallbackProps) {
  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="error-boundary-title">
        <p className="eyebrow">Runtime error</p>
        <h1 id="error-boundary-title">The admin shell stopped rendering</h1>
        <p className="error-message">{formatErrorMessage(error)}</p>
        <button className="primary-action" onClick={onReset} type="button">
          Try again
        </button>
      </section>
    </main>
  );
}

export function formatErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  if (typeof error === "string" && error.trim()) {
    return error;
  }

  return "An unexpected rendering error occurred.";
}
