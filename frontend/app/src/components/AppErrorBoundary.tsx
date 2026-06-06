import { Component, type ErrorInfo, type ReactNode } from "react";

type AppErrorBoundaryProps = {
  children: ReactNode;
};

type AppErrorBoundaryState = {
  error: Error | null;
};

export class AppErrorBoundary extends Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = {
    error: null,
  };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("React render failed:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="app-shell">
          <section className="mobile-frame error-frame">
            <header className="app-header">
              <div>
                <p className="app-kicker">前端运行错误</p>
                <h1>页面没有成功渲染</h1>
              </div>
            </header>

            <div className="error-panel">
              <strong>{this.state.error.name}</strong>
              <pre>{this.state.error.message}</pre>
              <p>把这段报错发出来，我们就能准确定位是哪一行出问题。</p>
            </div>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
