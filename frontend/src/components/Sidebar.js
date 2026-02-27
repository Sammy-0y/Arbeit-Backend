import { NavLink } from "react-router-dom";
import { useState } from "react";
import React from 'react';
import logo from '../assets/logo.png';
import "./sidebar.css";
const isMobile = window.innerWidth <= 768;

export default function Sidebar() {

  const [open, setOpen] = useState(false);

  return (
    <>
      <button
  className="menu-toggle text-white" // Add text-white here
  onClick={() => setOpen(true)}
>
        ☰
      </button>

      {/* OVERLAY */}
      {open && isMobile && (
  <div
    className="overlay"
    onClick={() => setOpen(false)}
  ></div>
)}

      {/* SIDEBAR */}
      <div className={`sidebar ${open ? "active" : ""}`}>

        {/* CLOSE BUTTON */}
        <button
          className="close-btn"
          onClick={() => setOpen(false)}
        >
          ✕
        </button>

        <h2 className="logo">
  <img 
    src={logo} 
    alt="Arbeit Logo" 
    style={{ width: '100%', maxWidth: '150px', display: 'block' }} 
  />
</h2>

        <NavLink to="/dashboard" onClick={() => setOpen(false)}>
  Dashboard
</NavLink>

<NavLink to="/clients" onClick={() => setOpen(false)}>
  Manage Clients
</NavLink>

<NavLink to="/jobs" onClick={() => setOpen(false)}>
  Job Requirements
</NavLink>

<NavLink to="/candidates" onClick={() => setOpen(false)}>
  Candidates
</NavLink>

<NavLink to="/governance" onClick={() => setOpen(false)}>
  Governance
</NavLink>

<NavLink to="/candidate-portal-management" onClick={() => setOpen(false)}>
  Portal Users
</NavLink>

      </div>
    </>
  );
}