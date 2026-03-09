import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  LayoutDashboard,
  Menu,
  Users,
  Briefcase,
  FileText,
  Settings,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  ArrowLeft,
  ArrowRight,
  TrendingUp,
  UserCog
} from "lucide-react";
import { NotificationBell } from '../components/notifications';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AdminDashboard = () => {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    clients: 0,
    jobs: 0,
    candidates: 0,
    interviews: null
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const [clientsRes, jobsRes, interviewStatsRes] = await Promise.all([
        axios.get(`${API}/clients`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/jobs`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/interviews/stats/pipeline`, { headers: { Authorization: `Bearer ${token}` } })
      ]);

      setStats({
        clients: clientsRes.data.length,
        jobs: jobsRes.data.length,
        candidates: jobsRes.data.reduce((sum, job) => sum + (job.candidates_count || 0), 0),
        interviews: interviewStatsRes.data
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen">
  <div className="container mx-auto px-4 py-6 md:p-8">
        {/* Welcome Card */}
<Card className="shadow-lg mb-6 rounded-2xl">
  <CardContent className="p-8">
    <div className="border-l-4 border-teal-500 pl-4">
      <h2 className="text-2xl font-semibold text-blue-900 mb-2">
        Welcome, {user?.name}!
      </h2>
      <p className="text-gray-600 text-lg">
        Full system access enabled. Manage clients, jobs, candidates, and interviews.
      </p>
    </div>
  </CardContent>
</Card>

{/* Stats Section */}
{/* Stats Section */}
{/* Stats Section */}
{/* Stats Section */}
{/* Stats Section */}
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mt-6 px-3 sm:px-0">

  {/* Clients */}
  <Card
  onClick={() => navigate("/clients")}
  className="p-3 sm:p-4 rounded-2xl bg-blue-100 border-l-4 border-blue-500 shadow-sm hover:shadow-md transition-all cursor-pointer hover:scale-[1.02]"
>

  <div className="flex justify-between items-start">
    <div>
      <h3 className="text-base font-semibold text-gray-800">
        Clients
      </h3>
      <p className="text-xs text-gray-500 mt-1">
        Total registered clients
      </p>
    </div>
    <Users className="h-5 w-5 text-blue-600" />
  </div>

  <div className="mt-2 text-2xl sm:text-3xl font-bold text-gray-900">
    {stats.clients}
  </div>

  <div className="mt-3 flex justify-end items-center text-xs text-blue-600">
    <span className="mr-1">View details</span>
    <ArrowRight className="h-4 w-4" />
  </div>

</Card>

  {/* Active Jobs */}
  <Card
    onClick={() => navigate("/jobs")}
    className="p-3 sm:p-4 rounded-2xl bg-green-50 border-l-4 border-green-500 shadow-sm hover:shadow-md transition-all cursor-pointer hover:scale-[1.02]"
  >
    <div className="flex justify-between items-start">
      <div>
        <h3 className="text-base font-semibold text-gray-800">
          Active Jobs
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Currently open positions
        </p>
      </div>
      <Briefcase className="h-6 w-6 text-emerald-600" />
    </div>

    <div className="mt-2 text-2xl sm:text-3xl font-bold text-gray-900">
      {stats.jobs}
    </div>

   <div className="mt-3 flex justify-end items-center text-xs text-emerald-600">
      <span className="mr-1">View details</span>
      <ArrowRight className="h-4 w-4" />
    </div>
  </Card>


  {/* Candidates */}
  <Card
    onClick={() => navigate("/candidates")}
    className="p-3 sm:p-4 rounded-2xl bg-purple-50 border-l-4 border-purple-500 shadow-sm hover:shadow-md transition-all cursor-pointer hover:scale-[1.02]"
  >
    <div className="flex justify-between items-start">
      <div>
        <h3 className="text-base font-semibold text-gray-800">
          Candidates
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Total applicants received
        </p>
      </div>
      <FileText className="h-6 w-6 text-purple-600" />
    </div>

    <div className="mt-2 text-2xl sm:text-3xl font-bold text-gray-900">
      {stats.candidates}
    </div>

    <div className="mt-3 flex justify-end items-center text-xs text-purple-600">
      <span className="mr-1">View details</span>
      <ArrowRight className="h-4 w-4" />
    </div>
  </Card>


  {/* Interviews */}
  <Card
    onClick={() => navigate("/interviews")}
    className="p-3 sm:p-4 rounded-2xl bg-orange-50 border-l-4 border-orange-500 shadow-sm hover:shadow-md transition-all cursor-pointer hover:scale-[1.02]"
  >
    <div className="flex justify-between items-start">
      <div>
        <h3 className="text-base font-semibold text-gray-800">
          Interviews
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Scheduled interviews
        </p>
      </div>
      <Calendar className="h-6 w-6 text-amber-600" />
    </div>

    <div className="mt-2 text-2xl sm:text-3xl font-bold text-gray-900">
      {stats.interviews?.total_interviews || 0}
    </div>

    <div className="mt-3 flex justify-end items-center text-xs text-amber-600">
      <span className="mr-1">View details</span>
      <ArrowRight className="h-4 w-4" />
    </div>
  </Card>

</div>
        {/* Interview Pipeline Widget */}
{stats.interviews && (
  <Card className="shadow-xl mt-6" data-testid="interview-pipeline-card">
            <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
              <CardTitle className="text-xl flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Interview Pipeline
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                <div 
                  className="text-center p-3 bg-amber-50 rounded-lg cursor-pointer hover:bg-amber-100 hover:shadow-md transition-all"
                  onClick={() => navigate('/interviews?status=Awaiting Candidate Confirmation')}
                  data-testid="pipeline-awaiting"
                >
                  <Clock className="h-6 w-6 mx-auto mb-1 text-amber-600" />
                  <p className="text-2xl font-bold text-amber-800">{stats.interviews.awaiting_confirmation}</p>
                  <p className="text-xs text-gray-600">Awaiting</p>
                </div>
                <div 
                  className="text-center p-3 bg-blue-50 rounded-lg cursor-pointer hover:bg-blue-100 hover:shadow-md transition-all"
                  onClick={() => navigate('/interviews?status=Confirmed')}
                  data-testid="pipeline-confirmed"
                >
                  <CheckCircle className="h-6 w-6 mx-auto mb-1 text-blue-600" />
                  <p className="text-2xl font-bold text-blue-800">{stats.interviews.confirmed}</p>
                  <p className="text-xs text-gray-600">Confirmed</p>
                </div>
                <div 
                  className="text-center p-3 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 hover:shadow-md transition-all"
                  onClick={() => navigate('/interviews?status=Scheduled')}
                  data-testid="pipeline-scheduled"
                >
                  <Calendar className="h-6 w-6 mx-auto mb-1 text-green-600" />
                  <p className="text-2xl font-bold text-green-800">{stats.interviews.scheduled}</p>
                  <p className="text-xs text-gray-600">Scheduled</p>
                </div>
                <div 
                  className="text-center p-3 bg-teal-50 rounded-lg cursor-pointer hover:bg-teal-100 hover:shadow-md transition-all"
                  onClick={() => navigate('/interviews?status=Completed')}
                  data-testid="pipeline-completed"
                >
                  <CheckCircle className="h-6 w-6 mx-auto mb-1 text-teal-600" />
                  <p className="text-2xl font-bold text-teal-800">{stats.interviews.completed}</p>
                  <p className="text-xs text-gray-600">Completed</p>
                </div>
                <div 
                  className="text-center p-3 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 hover:shadow-md transition-all"
                  onClick={() => navigate('/interviews?status=No Show')}
                  data-testid="pipeline-noshows"
                >
                  <XCircle className="h-6 w-6 mx-auto mb-1 text-red-600" />
                  <p className="text-2xl font-bold text-red-800">{stats.interviews.no_shows}</p>
                  <p className="text-xs text-gray-600">No Shows</p>
                </div>
                <div 
                  className="text-center p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 hover:shadow-md transition-all"
                  onClick={() => navigate('/interviews?status=Cancelled')}
                  data-testid="pipeline-cancelled"
                >
                  <XCircle className="h-6 w-6 mx-auto mb-1 text-gray-600" />
                  <p className="text-2xl font-bold text-gray-800">{stats.interviews.cancelled}</p>
                  <p className="text-xs text-gray-600">Cancelled</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
