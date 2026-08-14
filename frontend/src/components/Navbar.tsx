import React from 'react';
import { Link } from 'react-router-dom';

const Navbar: React.FC = () => {
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  };

  return (
    <nav className="bg-primary text-white p-4 flex justify-between items-center shadow-md">
      <Link to="/dashboard" className="text-xl font-semibold">
        Interview Coach
      </Link>
      <button onClick={handleLogout} className="bg-white text-primary px-3 py-1 rounded">
        Logout
      </button>
    </nav>
  );
};

export default Navbar;
