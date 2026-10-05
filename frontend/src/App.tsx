import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { isAuthed, clearToken } from "./lib/api";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ProfileEditor from "./pages/ProfileEditor";
import Bookings from "./pages/Bookings";
import CallLogs from "./pages/CallLogs";

function Guard({ children }: { children: React.ReactNode }) {
  return isAuthed() ? <>{children}</> : <Navigate to="/login" replace />;
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav className="nav">
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/profile">Profile</NavLink>
        <NavLink to="/bookings">Bookings</NavLink>
        <NavLink to="/calls">Call Logs</NavLink>
        <span style={{ flex: 1 }} />
        <button
          onClick={() => {
            clearToken();
            location.href = "/login";
          }}
        >
          Log out
        </button>
      </nav>
      <div className="container">{children}</div>
    </>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Guard>
            <Shell><Dashboard /></Shell>
          </Guard>
        }
      />
      <Route
        path="/profile"
        element={
          <Guard>
            <Shell><ProfileEditor /></Shell>
          </Guard>
        }
      />
      <Route
        path="/bookings"
        element={
          <Guard>
            <Shell><Bookings /></Shell>
          </Guard>
        }
      />
      <Route
        path="/calls"
        element={
          <Guard>
            <Shell><CallLogs /></Shell>
          </Guard>
        }
      />
    </Routes>
  );
}
