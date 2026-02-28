import { Outlet } from "react-router-dom";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";
import Sidebar from "../components/Sidebar";
export default function AdminLayout() {
  return (
  <div className="flex h-screen overflow-hidden bg-gray-100">
    
    {/* SIDEBAR */}
    <Sidebar />

    {/* RIGHT SIDE */}
    <div className="flex-1 flex flex-col overflow-y-auto">

      {/* PAGE CONTENT */}
      <div className="flex-1 w-full">
  <Outlet />
</div>

    </div>
  </div>
);
}