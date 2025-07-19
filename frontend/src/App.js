import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Components from './Components';

const {
  Header,
  Hero,
  Features,
  MembershipPlans,
  About,
  Trainers,
  Footer,
  LoginModal,
  SignupModal,
  MemberDashboard
} = Components;

function App() {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isSignupOpen, setIsSignupOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsLoggedIn(true);
    setIsLoginOpen(false);
  };

  const handleLogout = () => {
    setUser(null);
    setIsLoggedIn(false);
  };

  const LandingPage = () => (
    <div className="min-h-screen bg-black">
      <Header 
        onLoginClick={() => setIsLoginOpen(true)}
        onSignupClick={() => setIsSignupOpen(true)}
        isLoggedIn={isLoggedIn}
        user={user}
        onLogout={handleLogout}
      />
      <Hero onGetStarted={() => setIsSignupOpen(true)} />
      <Features />
      <MembershipPlans onSelectPlan={() => setIsSignupOpen(true)} />
      <About />
      <Trainers />
      <Footer />
      
      <LoginModal 
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLogin={handleLogin}
        onSwitchToSignup={() => {
          setIsLoginOpen(false);
          setIsSignupOpen(true);
        }}
      />
      
      <SignupModal 
        isOpen={isSignupOpen}
        onClose={() => setIsSignupOpen(false)}
        onSignup={handleLogin}
        onSwitchToLogin={() => {
          setIsSignupOpen(false);
          setIsLoginOpen(true);
        }}
      />
    </div>
  );

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={isLoggedIn ? <MemberDashboard user={user} onLogout={handleLogout} /> : <LandingPage />} 
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;