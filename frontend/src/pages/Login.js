import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import loginImage from "../assets/Login-Image.jpg";
import logo from "../assets/logo.png";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Lock, AlertTriangle } from 'lucide-react';

export const Login = () => {
  const navigate = useNavigate();
  const { login, changePassword } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Password change dialog state
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(email, password);

    if (result.success) {
      if (result.mustChangePassword) {
        // Store the current password for verification
        setCurrentPassword(password);
        setShowPasswordChange(true);
        toast.info('Please change your password before continuing');
      } else {
        toast.success('Login successful');
        navigate('/dashboard');
      }
    } else {
      toast.error(result.error || 'Login failed');
    }

    setLoading(false);
  };

  const handlePasswordChange = async () => {
    // Validate passwords
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    if (newPassword === currentPassword) {
      toast.error('New password must be different from current password');
      return;
    }
    
    setChangingPassword(true);
    
    const result = await changePassword(currentPassword, newPassword);
    
    if (result.success) {
      toast.success('Password changed successfully');
      setShowPasswordChange(false);
      navigate('/dashboard');
    } else {
      toast.error(result.error || 'Failed to change password');
    }
    
    setChangingPassword(false);
  };

  return (
  <div className="min-h-screen flex flex-col lg:flex-row relative">
  {/* Mobile Background */}
<div
  className="absolute inset-0 lg:hidden"
  style={{
    backgroundImage: `url(${loginImage})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
  }}
>
  <div className="absolute inset-0 bg-black/60"></div>
</div>

    {/* LEFT LOGIN SECTION */}
    <div className="relative z-10 w-full lg:w-1/2 flex items-center justify-center bg-transparent lg:bg-gray-50 px-8 py-12">

      <div className="w-full max-w-md bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl p-10">

        {/* LOGO */}
        <img 
          src={logo}   // 🔥 CHANGE LOGO HERE
          alt="Company Logo"
          className="h-16 mb-10 mx-auto"
        />

        <h2 className="text-3xl font-bold text-white lg:text-gray-900 mb-2">
         Workforce Management Made Simple.
        </h2>

        <p className="text-gray-200 lg:text-gray-500 mb-8">
          Please enter your details
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-white lg:text-gray-700 mb-2">
              Email address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Example@gmail.com"
              required
              className="w-full bg-white/20 lg:bg-white border border-white/30 lg:border-gray-300 rounded-md px-4 py-3 text-white lg:text-gray-900 placeholder-white lg:placeholder-gray-400 focus:outline-none"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-white lg:text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password Here"
              required
              className="w-full bg-white/20 lg:bg-white border border-white/30 lg:border-gray-300 rounded-md px-4 py-3 text-white lg:text-gray-900 placeholder-white lg:placeholder-gray-400 focus:outline-none"
            />
          </div>

          {/* Button */}
          <button
            type="submit"
            className="w-full bg-purple-600 text-white py-3 rounded-md font-medium hover:bg-purple-700 transition duration-200"
          >
            Sign in
          </button>

        </form>

      </div>
    </div>


    {/* RIGHT IMAGE SECTION */}
   <div className="hidden lg:block lg:w-1/2 h-screen relative">
   <img
    src={loginImage}
    alt="Login Illustration"
    className="absolute inset-0 w-full h-full object-cover"
   />
   </div>

  </div>
);
};