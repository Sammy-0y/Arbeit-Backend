import { NavLink } from "react-router-dom";import sidebarBg from "../assets/sidebar-bg.png";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  Shield,
  UserCog,
  LogOut,
  ArrowLeft
} from "lucide-react";
export default function Sidebar({ closeSidebar }) {
  const navigate = useNavigate();
const { logout } = useAuth();

const handleLogout = () => {
  logout();
  navigate("/login");
};
  return (
  <div
className={`fixed md:static top-0 left-0 h-screen w-56 flex flex-col
bg-no-repeat bg-top bg-cover z-50
transform transition-transform duration-300`}
style={{ backgroundImage: `url(${sidebarBg})` }}
>
    
    {/* MENU */}
    <div className="flex-1 px-6 pt-52">
      <nav className="flex flex-col space-y-4">
        <NavLink to="/dashboard" onClick={closeSidebar} className={({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-md"
      : "text-white hover:bg-blue-500/20"
  }`
}>
  <LayoutDashboard size={18} />
          Dashboard
        </NavLink>

        <NavLink to="/clients" onClick={closeSidebar} className={({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-md"
      : "text-white hover:bg-blue-500/20"
  }`
}>
  <Users size={18} />
          Clients
        </NavLink>

        <NavLink to="/jobs" onClick={closeSidebar} className={({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-md"
      : "text-white hover:bg-blue-500/20"
  }`
}>
  <Briefcase size={18} />
          Job Requirements
        </NavLink>

        <NavLink to="/candidates" onClick={closeSidebar} className={({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-md"
      : "text-white hover:bg-blue-500/20"
  }`
}>
  <FileText size={18} />
          Candidates
        </NavLink>

        <NavLink to="/governance" onClick={closeSidebar} className={({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-md"
      : "text-white hover:bg-blue-500/20"
  }`
}>
  <Shield size={18} />
          Governance
        </NavLink>

        <NavLink to="/candidate-portal-management" onClick={closeSidebar} className={({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-md"
      : "text-white hover:bg-blue-500/20"
  }`
}>
  <UserCog size={18} />
          Portal Users
        </NavLink>
      </nav>
    </div>

  {/* Mobile Close Menu Button */}
<button
  onClick={closeSidebar}
  className="md:hidden mx-6 mb-10 py-2 px-4 
             rounded-xl 
             bg-white/60 backdrop-blur-md 
             border border-gray-200 
             hover:bg-white hover:shadow-sm 
             transition-all duration-200 
             flex items-center justify-center gap-2 
             text-gray-600 text-sm font-medium"
>
  <ArrowLeft size={16} />
  Close Menu
</button>
    {/* LOGOUT AT BOTTOM */}
<div className="mt-auto px-6 pb-10">
  <button
    onClick={handleLogout}
    className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl bg-red-500 text-white font-medium hover:bg-red-600 transition"
  >
    <LogOut size={18} />
    Logout
  </button>
</div>

  </div>
);
}