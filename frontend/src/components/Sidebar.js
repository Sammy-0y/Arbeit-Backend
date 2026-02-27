import { NavLink } from "react-router-dom";
import "./sidebar.css";

export default function Sidebar() {
  return (
    <div className="sidebar">
      <h2 className="logo">arbeit</h2>

      <NavLink to="/dashboard">Dashboard</NavLink>
      <NavLink to="/clients">Manage Clients</NavLink>
      <NavLink to="/jobs">Job Requirements</NavLink>
      <NavLink to="/candidates">Candidates</NavLink>
      <NavLink to="/governance">Governance</NavLink>
      <NavLink to="/candidate-portal-management">Portal Users</NavLink>
    </div>
  );
}