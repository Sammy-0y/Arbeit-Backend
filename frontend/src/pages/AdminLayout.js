import { Outlet } from "react-router-dom";
import { useState } from "react";
import { Menu, X, LayoutDashboard } from "lucide-react";
import Sidebar from "../components/Sidebar";
import { NotificationBell } from "../components/notifications";
import { useAuth } from "../contexts/AuthContext";
export default function AdminLayout() {
  const { isClientUser } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  return (
  <div className="flex min-h-screen bg-[#eef4ff]">

    {/* Desktop Sidebar */}
    <div className="hidden md:flex md:w-64 md:fixed md:inset-y-0 md:left-0">
      <Sidebar />
    </div>

    {/* Mobile Sidebar Overlay */}
    {isOpen && (
      <div className="fixed inset-0 z-50 md:hidden">
        <div
          className="absolute inset-0 bg-black/30"
          onClick={() => setIsOpen(false)}
        />
        <div className="absolute top-0 left-0 w-[260px] h-full">
          <Sidebar closeSidebar={() => setIsOpen(false)} />
        </div>
      </div>
    )}
    {/* Main Content */}
<div className="flex-1 md:ml-64 flex flex-col">
  {/* Mobile Header */}
  {/* Mobile Header */}
<div className="fixed top-0 left-0 right-0 md:left-56 z-40">
  <div className="
  bg-[#243b8f]
  text-white
  rounded-b-[24px]
  px-6 md:px-8
  py-4
  shadow-md
  flex items-center justify-between
">

    {/* Left Side */}
    <div className="flex items-center gap-3">

      <button
        onClick={() => setIsOpen(true)}
        className="md:hidden p-2 rounded-lg hover:bg-white/10"
      >
        <Menu size={22} />
      </button>

      <LayoutDashboard className="h-5 w-5 text-blue-200" />

      <span className="font-semibold">
         {isClientUser ? "Client Hiring Portal" : "Admin Dashboard"}
      </span>

    </div>

    {/* Right Side */}
    <div className="flex items-center gap-4">

      {!isClientUser && <NotificationBell />}

      <span className="text-sm text-blue-200">
        Welcome back
      </span>

    </div>

  </div>

</div>
  {/* Page Content */}
  <div className="px-4 py-6 pt-24 md:pt-28 md:p-6">
    <Outlet />
  </div>

</div>

  </div>
);
}