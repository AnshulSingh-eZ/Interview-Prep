import React from "react";
import { Link, useNavigate } from "react-router-dom";

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/75 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-3">
        <Link to={token ? "/dashboard" : "/login"} className="text-lg font-semibold tracking-tight text-white">
          Interview Coach
        </Link>
        {token ? (
          <nav className="flex items-center gap-1 text-sm">
            <Link to="/resume" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-white/5 hover:text-white">
              Resume
            </Link>
            <Link to="/companies" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-white/5 hover:text-white">
              Practice
            </Link>
            <button onClick={handleLogout} className="btn-ghost !py-2 !px-3">
              Logout
            </button>
          </nav>
        ) : (
          <Link to="/login" className="btn-ghost !py-2 !px-3">
            Login
          </Link>
        )}
      </div>
    </header>
  );
};

export default Navbar;
