import { Outlet } from "react-router-dom";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";
import Sidebar from "../components/Sidebar";
export default function AdminLayout() {
  const [isOpen, setIsOpen] = useState(false);
  return (
  <div className="relative flex h-screen bg-blue-900">

    {/* MOBILE HAMBURGER */}
    {!isOpen && (
  <button
    className="md:hidden fixed top-4 left-4 z-50"
    onClick={() => setIsOpen(true)}
  >
    <Menu size={28} className="text-white" />
  </button>
)}

    {/* SIDEBAR */}
    {/* SIDEBAR */}
<div
  className={`
fixed top-4 bottom-4 left-0 md:left-0 min-h-screen w-56 bg-slate-900 text-slate-200 z-40
rounded-r-2xl shadow-2xl border-r-0
transform transition-transform duration-300
${isOpen ? "translate-x-0" : "-translate-x-full"}
md:translate-x-0 md:fixed
`}
>
      {/* Close Button (Mobile Only) */}
      <div className="md:hidden absolute top-4 right-4 z-50">
        <button onClick={() => setIsOpen(false)}>
          <X size={24} />
        </button>
      </div>

      <Sidebar closeSidebar={() => setIsOpen(false)} />
    </div>

    {/* OVERLAY */}
    {isOpen && (
      <div
        className="fixed inset-0 bg-black bg-opacity-40 md:hidden z-30"
        onClick={() => setIsOpen(false)}
      />
    )}

    {/* RIGHT SIDE CONTENT */}
    <div className="flex-1 flex flex-col overflow-y-auto">
      <div className="flex-1 w-full">
        <Outlet />
      </div>
    </div>

  </div>
);
}