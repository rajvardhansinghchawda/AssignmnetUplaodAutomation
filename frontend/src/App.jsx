import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Setup from './pages/Setup';
import Status from './pages/Status';
import Login from './pages/Login';
import Navbar from './components/Navbar';
import { AuthProvider, useAuth } from './context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { token, isLoading } = useAuth();
  if (isLoading) return null;
  return token ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-background text-on_background font-sans selection:bg-primary_container selection:text-on_primary_container">
          <Navbar />
          <main className="max-w-4xl mx-auto px-6 py-10 overflow-x-hidden">
            <Routes>
              <Route path="/" element={<Navigate to="/setup" replace />} />
              <Route path="/login" element={<Login />} />
              <Route path="/setup" element={
                <ProtectedRoute><Setup /></ProtectedRoute>
              } />
              <Route path="/status" element={
                <ProtectedRoute><Status /></ProtectedRoute>
              } />
              <Route path="/dashboard" element={<Navigate to="/setup" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
