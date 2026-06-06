import type { SyntheticEvent } from "react";

export type AuthMode = "login" | "register";

type AuthPanelProps = {
  authMode: AuthMode;
  username: string;
  password: string;
  status: string;
  isSubmitting: boolean;
  onAuthModeChange: (mode: AuthMode) => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: SyntheticEvent<HTMLFormElement>) => void;
};

export function AuthPanel({
  authMode,
  username,
  password,
  status,
  isSubmitting,
  onAuthModeChange,
  onUsernameChange,
  onPasswordChange,
  onSubmit,
}: AuthPanelProps) {
  return (
    <section className="mobile-frame auth-frame">
      <header className="app-header">
        <div>
          <p className="app-kicker">熊心壮职</p>
          <h1>{authMode === "login" ? "欢迎回来" : "创建身份"}</h1>
        </div>
      </header>

      <form className="auth-form" onSubmit={onSubmit}>
        <div className="auth-tabs">
          <button
            className={authMode === "login" ? "is-active" : ""}
            type="button"
            onClick={() => onAuthModeChange("login")}
          >
            登录
          </button>
          <button
            className={authMode === "register" ? "is-active" : ""}
            type="button"
            onClick={() => onAuthModeChange("register")}
          >
            注册
          </button>
        </div>

        <label className="input-box">
          <span>玩家名</span>
          <input
            value={username}
            onChange={(event) => onUsernameChange(event.target.value)}
            autoComplete="username"
            placeholder="例如：test01"
          />
        </label>

        <label className="input-box">
          <span>密码</span>
          <input
            value={password}
            onChange={(event) => onPasswordChange(event.target.value)}
            autoComplete="current-password"
            type="password"
            placeholder="测试阶段可先随意填写"
          />
        </label>

        <p className="form-status">{status}</p>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "处理中..." : authMode === "login" ? "进入公司" : "创建身份"}
        </button>
      </form>
    </section>
  );
}
