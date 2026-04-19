import { Link, useLocation, useNavigate } from 'react-router-dom';
import { GraduationCap, LogOut, Zap, Square, Loader2, Settings, PieChart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getActiveRun, stopRun } from '../api';
import React, { useState, useEffect } from 'react';

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeRunId, setActiveRunId] = useState(null);
  const [isStopping, setIsStopping] = useState(false);

  // Poll for active runs every 5 seconds if logged in
  useEffect(() => {
    if (!user) {
      setActiveRunId(null);
      return;
    }

    const checkActive = async () => {
      // Don't poll if page is hidden
      if (document.visibilityState === 'hidden') return;
      
      try {
        const res = await getActiveRun();
        if (res.data && res.data.id) {
          setActiveRunId(res.data.id);
        } else {
          setActiveRunId(null);
        }
      } catch (err) {
        setActiveRunId(null);
      }
    };

    checkActive();
    const interval = setInterval(checkActive, 15000); // Poll every 15 seconds to reduce background requests
    return () => clearInterval(interval);
  }, [user]);

  const handleStop = async (e) => {
    e.preventDefault();
    if (!activeRunId || isStopping) return;
    
    if (!window.confirm("Stop the running script?")) return;

    setIsStopping(true);
    try {
      await stopRun(activeRunId);
      setActiveRunId(null);
    } catch (err) {
      console.error("Stop error:", err);
    } finally {
      setIsStopping(false);
    }
  };

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
                className={`px-3 md:px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  location.pathname === '/setup'
                    ? 'bg-primary_container text-on_primary_container shadow-sm'
                    : 'text-on_surface hover:bg-surface_container'
                }`}
              >
                <Settings className="w-4 h-4 md:hidden" />
                <span className="hidden md:inline">Setup</span>
              </Link>
              <Link
                to="/status"
                className={`px-3 md:px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  location.pathname === '/status'
                    ? 'bg-primary_container text-on_primary_container shadow-sm'
                    : 'text-on_surface hover:bg-surface_container'
                }`}
              >
                <PieChart className="w-4 h-4 md:hidden" />
                <span className="hidden md:inline">Status</span>
              </Link>

              {activeRunId && (
                <div className="flex items-center gap-1">
                  <Link
                    to="/running"
                    state={{ runId: activeRunId }} 
                    className={`flex items-center gap-1.5 px-2 md:px-3 py-1.5 rounded-l-lg text-[10px] md:text-xs font-bold transition-all border border-primary/20 bg-primary/5 text-primary animate-pulse hover:bg-primary/10`}
                  >
                    <Zap className="w-3 md:w-3.5 h-3 md:h-3.5 fill-current" />
                    <span className="hidden sm:inline">Running</span>
                  </Link>
                  <button
                    onClick={handleStop}
                    disabled={isStopping}
                    title="Stop Script"
                    className="p-1.5 h-[30px] rounded-r-lg bg-error/10 text-error border border-error/20 hover:bg-error/20 transition-all flex items-center justify-center"
                  >
                    {isStopping ? <Loader2 className="w-3 h-3 animate-spin" /> : <Square className="w-3 h-3 fill-current" />}
                  </button>
                </div>
              )}
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
