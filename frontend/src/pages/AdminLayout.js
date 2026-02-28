import { Outlet } from "react-router-dom";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";
import Sidebar from "../components/Sidebar";
export default function AdminLayout() {
  const [isOpen, setIsOpen] = useState(false);
  return (
  <div className="relative flex h-screen bg-gray-100">

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
    fixed top-0 left-0 h-full w-64 bg-white z-40
    transform transition-transform duration-300
    ${isOpen ? "translate-x-0" : "-translate-x-full"}
    md:translate-x-0 md:static
  `}
>
      {/* Close Button (Mobile Only) */}
      <div className="md:hidden flex justify-end p-4 bg-white">
        <button onClick={() => setIsOpen(false)}>
          <X size={24} />
        </button>
      </div>

      <Sidebar closeSidebar={() => setIsOpen(false)} />
    </div>

    {/* OVERLAY */}
    {isOpen && (
      <div
        className="fixed inset-0 bg-black bg-opacity-40 md:hidden"
        onClick={() => setIsOpen(false)}
      />
    )}

    {/* RIGHT SIDE CONTENT */}
    <div className="flex-1 flex flex-col overflow-y-auto ">
      <div className="flex-1 w-full">
        <Outlet />
      </div>
    </div>

  </div>
);
}