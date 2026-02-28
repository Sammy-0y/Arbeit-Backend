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
  <div className="w-64 bg-[#faf7f1] shadow-lg h-full p-6 flex flex-col">
    {/* LOGO */}
    <div className="flex justify-center mb-8">
  <img
  src={logo}
  alt="Arbeit Logo"
  className="h-12 object-contain"
/>
</div>
    {/* MENU */}
    <div className="flex-1">
      <nav className="flex flex-col space-y-4 text-gray-700 font-medium">
        <NavLink to="/dashboard" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive ? "bg-blue-100 text-blue-700 font-semibold" : "hover:bg-gray-100"
          }`
        }>
          Dashboard
        </NavLink>

        <NavLink to="/clients" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive ? "bg-blue-100 text-blue-700 font-semibold" : "hover:bg-gray-100"
          }`
        }>
          Clients
        </NavLink>

        <NavLink to="/jobs" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive ? "bg-blue-100 text-blue-700 font-semibold" : "hover:bg-gray-100"
          }`
        }>
          Job Requirements
        </NavLink>

        <NavLink to="/candidates" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive ? "bg-blue-100 text-blue-700 font-semibold" : "hover:bg-gray-100"
          }`
        }>
          Candidates
        </NavLink>

        <NavLink to="/governance" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive ? "bg-blue-100 text-blue-700 font-semibold" : "hover:bg-gray-100"
          }`
        }>
          Governance
        </NavLink>

        <NavLink to="/candidate-portal-management" onClick={closeSidebar} className={({ isActive }) =>
          `px-3 py-2 rounded-md ${
            isActive ? "bg-blue-100 text-blue-700 font-semibold" : "hover:bg-gray-100"
          }`
        }>
          Portal Users
        </NavLink>
      </nav>
    </div>

    {/* LOGOUT AT BOTTOM */}
    <button
      onClick={handleLogout}
      className="mt-auto mb-06 bg-red-50 text-red-600 py-2 rounded-md hover:bg-red-100 font-medium"
    >
      Logout
    </button>

  </div>
);
}