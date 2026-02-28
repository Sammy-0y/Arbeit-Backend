import { NavLink } from "react-router-dom";
import logo from "../assets/logo.png";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Sidebar({ closeSidebar }) {
  const navigate = useNavigate();
const { logout } = useAuth();

const handleLogout = () => {
  logout();
  navigate("/login");
};
  return (
  <div className="w-56 bg-slate-900 text-slate-200 h-full p-6 flex flex-col rounded-r-2xl shadow-2xl">
    {/* LOGO */}
    <div className="flex justify-center mb-8 bg-slate-800 rounded-lg p-3">
  <img
  src={logo}
  alt="Arbeit Logo"
  className="h-12 object-contain"
/>
</div>
    {/* MENU */}
    <div className="flex-1">
      <nav className="flex flex-col space-y-4 text-slate-300 font-medium">
        <NavLink to="/dashboard" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive 
  ? "bg-blue-600 text-white font-semibold" 
  : "hover:bg-slate-800"
          }`
        }>
          Dashboard
        </NavLink>

        <NavLink to="/clients" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive 
  ? "bg-blue-600 text-white font-semibold" 
  : "hover:bg-slate-800"
          }`
        }>
          Clients
        </NavLink>

        <NavLink to="/jobs" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive 
  ? "bg-blue-600 text-white font-semibold" 
  : "hover:bg-slate-800"
          }`
        }>
          Job Requirements
        </NavLink>

        <NavLink to="/candidates" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive 
  ? "bg-blue-600 text-white font-semibold" 
  : "hover:bg-slate-800"
          }`
        }>
          Candidates
        </NavLink>

        <NavLink to="/governance" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive 
  ? "bg-blue-600 text-white font-semibold" 
  : "hover:bg-slate-800"
          }`
        }>
          Governance
        </NavLink>

        <NavLink to="/candidate-portal-management" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive 
  ? "bg-blue-600 text-white font-semibold" 
  : "hover:bg-slate-800"
          }`
        }>
          Portal Users
        </NavLink>
      </nav>
    </div>

    {/* LOGOUT AT BOTTOM */}
    <button
      onClick={handleLogout}
      className="mt-auto bg-red-600 hover:bg-red-700 text-white py-2 rounded-md font-medium"
    >
      Logout
    </button>

  </div>
);
}