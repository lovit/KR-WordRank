import { Link, useLocation } from "react-router-dom";

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { path: "/", label: "소개" },
  { path: "/how-it-works", label: "동작 원리" },
  { path: "/cli", label: "CLI" },
  { path: "/api", label: "API · 설치" },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <>
      <nav>
        <div className="container">
          <Link to="/" className="brand">
            KR-WordRank
          </Link>
          {navItems.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              style={{ fontWeight: location.pathname === path ? 600 : undefined }}
            >
              {label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="container">{children}</main>
    </>
  );
}
