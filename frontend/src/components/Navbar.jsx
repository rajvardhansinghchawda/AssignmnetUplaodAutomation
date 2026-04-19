import { Link, useLocation, useNavigate } from 'react-router-dom';
import { GraduationCap, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-surface/80 border-b border-surface_container_high px-2">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary_container flex items-center justify-center text-on_primary_container shadow-sm">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg font-display font-semibold text-on_background tracking-tight">
              PIEMR Auto-Uploader
            </h1>
            <p className="text-xs text-on_surface_variant">System Controller</p>
          </div>
        </div>

        <nav className="flex items-center gap-2">
          {user ? (
            <>
              <Link
                to="/setup"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  location.pathname === '/setup'
                    ? 'bg-primary_container text-on_primary_container shadow-sm'
                    : 'text-on_surface hover:bg-surface_container'
                }`}
              >
                Setup
              </Link>
              <Link
                to="/status"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  location.pathname === '/status'
                    ? 'bg-primary_container text-on_primary_container shadow-sm'
                    : 'text-on_surface hover:bg-surface_container'
                }`}
              >
                Status
              </Link>
              <div className="h-6 w-[1px] bg-outline_variant mx-1" />
              <div className="flex items-center gap-3 pl-2">
                <div className="hidden md:flex flex-col items-end">
                  <span className="text-[10px] font-bold text-on_surface_variant uppercase tracking-wider">User</span>
                  <span className="text-sm font-medium text-on_background truncate max-w-[120px]">
                    {user.full_name || user.email.split('@')[0]}
                  </span>
                </div>
                {user.picture ? (
                  <img 
                    src={user.picture} 
                    alt="Profile" 
                    className="w-9 h-9 rounded-full border border-primary/20 shadow-sm"
                  />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-surface_container_highest border border-outline_variant flex items-center justify-center text-on_surface_variant text-xs font-bold">
                    {user.email[0].toUpperCase()}
                  </div>
                )}
                <button 
                  onClick={handleLogout}
                  className="p-2 ml-1 rounded-lg text-on_surface_variant hover:bg-surface_container hover:text-error transition-all"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </>
          ) : (
            <Link
              to="/login"
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                location.pathname === '/login'
                  ? 'text-primary'
                  : 'text-on_surface hover:bg-surface_container'
              }`}
            >
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
