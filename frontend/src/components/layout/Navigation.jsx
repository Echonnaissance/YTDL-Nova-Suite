import { NavLink } from "react-router-dom";
import ThemeToggle from "../common/ThemeToggle";
import "./Navigation.css";

export default function Navigation() {
  return (
    <header className="navigation" role="banner">
      <nav className="nav-container" aria-label="Main navigation">
        <div className="nav-brand">
          <NavLink to="/" aria-label="Universal Media Downloader - Home">
            <span className="brand-icon" aria-hidden="true">
              ⬇️
            </span>
            <span className="brand-text">UMD</span>
          </NavLink>
        </div>
        <ul className="nav-links" role="menubar">
          <li role="none">
            <NavLink
              to="/"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              role="menuitem"
              end
            >
              <span className="nav-icon" aria-hidden="true">
                🏠
              </span>
              <span>Home</span>
            </NavLink>
          </li>
          <li role="none">
            <NavLink
              to="/download"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              role="menuitem"
            >
              <span className="nav-icon" aria-hidden="true">
                ⬇️
              </span>
              <span>Download</span>
            </NavLink>
          </li>
          <li role="none">
            <NavLink
              to="/history"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              role="menuitem"
            >
              <span className="nav-icon" aria-hidden="true">
                📋
              </span>
              <span>History</span>
            </NavLink>
          </li>
          <li role="none">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              role="menuitem"
            >
              <span className="nav-icon" aria-hidden="true">
                ⚙️
              </span>
              <span>Settings</span>
            </NavLink>
          </li>
          <li role="none">
            <NavLink
              to="/api-docs"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              role="menuitem"
            >
              <span className="nav-icon" aria-hidden="true">
                📚
              </span>
              <span>API</span>
            </NavLink>
          </li>
        </ul>
        <ThemeToggle />
      </nav>
    </header>
  );
}
