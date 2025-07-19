import React, { useState, useEffect } from 'react';

// Header Component
const Header = ({ onLoginClick, onSignupClick, isLoggedIn, user, onLogout }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`fixed w-full z-50 transition-all duration-300 ${
      isScrolled ? 'bg-black/90 backdrop-blur-sm' : 'bg-transparent'
    }`}>
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <span className="text-white font-bold text-xl">Alphalete Athletics</span>
          </div>
          
          <nav className="hidden md:flex space-x-8">
            <a href="#home" className="text-white hover:text-red-500 transition-colors">Home</a>
            <a href="#features" className="text-white hover:text-red-500 transition-colors">Features</a>
            <a href="#membership" className="text-white hover:text-red-500 transition-colors">Membership</a>
            <a href="#about" className="text-white hover:text-red-500 transition-colors">About</a>
            <a href="#trainers" className="text-white hover:text-red-500 transition-colors">Trainers</a>
          </nav>
          
          <div className="flex space-x-4">
            {isLoggedIn ? (
              <div className="flex items-center space-x-4">
                <span className="text-white">Welcome, {user?.name}</span>
                <button 
                  onClick={onLogout}
                  className="px-4 py-2 text-white border border-red-500 rounded-lg hover:bg-red-500 transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              <>
                <button 
                  onClick={onLoginClick}
                  className="px-4 py-2 text-white border border-white rounded-lg hover:bg-white hover:text-black transition-colors"
                >
                  Login
                </button>
                <button 
                  onClick={onSignupClick}
                  className="px-4 py-2 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg hover:from-red-600 hover:to-orange-600 transition-all"
                >
                  Join Now
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

// Hero Component
const Hero = ({ onGetStarted }) => {
  return (
    <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1654703680091-010855f522e8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHxneW0lMjBpbnRlcmlvcnxlbnwwfHx8YmxhY2t8MTc1Mjg4NzA3OXww&ixlib=rb-4.1.0&q=85')`
        }}
      />
      <div className="absolute inset-0 bg-black/60" />
      
      <div className="relative z-10 text-center max-w-4xl mx-auto px-6">
        <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
          Transform Your
          <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent"> Body</span>
        </h1>
        <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-2xl mx-auto">
          Join Alphalete Athletics Club - Where champions are made. Premium equipment, expert trainers, and a community that pushes you to excellence.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button 
            onClick={onGetStarted}
            className="px-8 py-4 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg text-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all transform hover:scale-105"
          >
            Start Your Journey
          </button>
          <button className="px-8 py-4 border-2 border-white text-white rounded-lg text-lg font-semibold hover:bg-white hover:text-black transition-all">
            Take a Tour
          </button>
        </div>
      </div>
    </section>
  );
};

// Features Component
const Features = () => {
  const features = [
    {
      title: "Premium Equipment",
      description: "State-of-the-art fitness equipment from leading brands",
      image: "https://images.unsplash.com/photo-1646656130630-07af3a262a9b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwxfHxmaXRuZXNzJTIwZXF1aXBtZW50fGVufDB8fHxibGFja3wxNzUyODg3MDg2fDA&ixlib=rb-4.1.0&q=85",
      icon: "🏋️"
    },
    {
      title: "Expert Trainers",
      description: "Certified personal trainers to guide your fitness journey",
      image: "https://images.unsplash.com/photo-1637666067348-7303e7007363?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwzfHxneW0lMjBpbnRlcmlvcnxlbnwwfHx8YmxhY2t8MTc1Mjg4NzA3OXww&ixlib=rb-4.1.0&q=85",
      icon: "👨‍💪"
    },
    {
      title: "Modern Facilities",
      description: "Spacious, clean, and modern gym environment",
      image: "https://images.unsplash.com/photo-1649591833478-15cd1060e137?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHxneW0lMjBpbnRlcmlvcnxlbnwwfHx8YmxhY2t8MTc1Mjg4NzA3OXww&ixlib=rb-4.1.0&q=85",
      icon: "🏢"
    },
    {
      title: "24/7 Access",
      description: "Train whenever you want with round-the-clock access",
      image: "https://images.unsplash.com/photo-1637666123723-1bea229bd054?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwyfHxmaXRuZXNzJTIwZXF1aXBtZW50fGVufDB8fHxibGFja3wxNzUyODg3MDg2fDA&ixlib=rb-4.1.0&q=85",
      icon: "🕐"
    }
  ];

  return (
    <section id="features" className="py-20 bg-gray-900">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Why Choose <span className="text-red-500">Alphalete</span>?
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Experience the difference with our world-class facilities and services
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="group cursor-pointer">
              <div className="relative overflow-hidden rounded-xl bg-gray-800 p-6 h-full hover:bg-gray-700 transition-all duration-300 transform hover:scale-105">
                <div className="relative z-10">
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
                <div 
                  className="absolute inset-0 bg-cover bg-center opacity-10 group-hover:opacity-20 transition-opacity"
                  style={{ backgroundImage: `url('${feature.image}')` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Membership Plans Component
const MembershipPlans = ({ onSelectPlan }) => {
  const plans = [
    {
      name: "Student",
      price: "$29",
      period: "/month",
      description: "Perfect for students with valid ID",
      features: [
        "Access to all equipment",
        "Basic group classes",
        "Locker room access",
        "Mobile app access",
        "Student ID required"
      ],
      popular: false,
      color: "from-blue-500 to-blue-600"
    },
    {
      name: "Monthly",
      price: "$59",
      period: "/month",
      description: "Most popular choice for fitness enthusiasts",
      features: [
        "All Student features",
        "Premium group classes",
        "1 personal training session",
        "Nutrition consultation",
        "Guest passes (2/month)"
      ],
      popular: true,
      color: "from-red-500 to-orange-500"
    },
    {
      name: "Custom",
      price: "Custom",
      period: "pricing",
      description: "Tailored solutions for your specific needs",
      features: [
        "Personalized training plan",
        "Unlimited personal training",
        "Nutrition & meal planning",
        "Priority booking",
        "Exclusive member events"
      ],
      popular: false,
      color: "from-purple-500 to-purple-600"
    }
  ];

  return (
    <section id="membership" className="py-20 bg-black">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Choose Your <span className="text-red-500">Plan</span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Flexible membership options designed to fit your lifestyle and goals
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div key={index} className={`relative group ${plan.popular ? 'scale-105' : ''}`}>
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-red-500 to-orange-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </div>
              )}
              
              <div className={`bg-gray-900 rounded-2xl p-8 h-full border-2 ${
                plan.popular ? 'border-red-500' : 'border-gray-700'
              } hover:border-red-500 transition-all duration-300 transform hover:scale-105`}>
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="flex items-baseline justify-center mb-4">
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    <span className="text-gray-400 ml-1">{plan.period}</span>
                  </div>
                  <p className="text-gray-400">{plan.description}</p>
                </div>
                
                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center text-gray-300">
                      <span className="text-green-500 mr-3">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
                
                <button 
                  onClick={onSelectPlan}
                  className={`w-full py-3 rounded-lg font-semibold transition-all duration-300 ${
                    plan.popular 
                      ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white hover:from-red-600 hover:to-orange-600' 
                      : 'border-2 border-gray-600 text-white hover:border-red-500 hover:bg-red-500'
                  }`}
                >
                  Choose {plan.name}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// About Component
const About = () => {
  return (
    <section id="about" className="py-20 bg-gray-900">
      <div className="container mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              About <span className="text-red-500">Alphalete Athletics</span>
            </h2>
            <p className="text-xl text-gray-400 mb-6">
              Founded with a vision to create the ultimate fitness experience, Alphalete Athletics Club combines cutting-edge equipment with expert guidance to help you achieve your goals.
            </p>
            <p className="text-lg text-gray-400 mb-8">
              Our state-of-the-art facility features premium equipment, spacious workout areas, and a community of dedicated fitness enthusiasts. Whether you're a beginner or a seasoned athlete, we provide the tools and support you need to succeed.
            </p>
            
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-red-500 mb-2">500+</div>
                <div className="text-gray-400">Active Members</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-red-500 mb-2">10+</div>
                <div className="text-gray-400">Expert Trainers</div>
              </div>
            </div>
          </div>
          
          <div className="relative">
            <img 
              src="https://images.unsplash.com/photo-1637666095575-c460a3aae9f0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwzfHxmaXRuZXNzJTIwZXF1aXBtZW50fGVufDB8fHxibGFja3wxNzUyODg3MDg2fDA&ixlib=rb-4.1.0&q=85"
              alt="About Alphalete Athletics"
              className="rounded-2xl shadow-2xl"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

// Trainers Component
const Trainers = () => {
  const trainers = [
    {
      name: "Alex Rodriguez",
      specialty: "Strength Training",
      experience: "8 years",
      image: "https://images.unsplash.com/photo-1594736797933-d0cc4618073d?w=400&h=400&fit=crop&crop=face",
      bio: "Specializes in powerlifting and strength conditioning"
    },
    {
      name: "Sarah Chen",
      specialty: "HIIT & Cardio",
      experience: "6 years",
      image: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
      bio: "Expert in high-intensity training and weight loss"
    },
    {
      name: "Marcus Johnson",
      specialty: "Bodybuilding",
      experience: "10 years",
      image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
      bio: "Professional bodybuilder and nutrition specialist"
    }
  ];

  return (
    <section id="trainers" className="py-20 bg-black">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Meet Our <span className="text-red-500">Trainers</span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Our certified trainers are here to guide you every step of the way
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {trainers.map((trainer, index) => (
            <div key={index} className="bg-gray-900 rounded-2xl p-6 text-center hover:bg-gray-800 transition-colors group">
              <div className="relative mb-6">
                <img 
                  src={trainer.image}
                  alt={trainer.name}
                  className="w-32 h-32 rounded-full mx-auto object-cover border-4 border-red-500 group-hover:scale-105 transition-transform"
                />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{trainer.name}</h3>
              <p className="text-red-500 font-semibold mb-2">{trainer.specialty}</p>
              <p className="text-gray-400 mb-4">{trainer.experience} experience</p>
              <p className="text-gray-400 text-sm">{trainer.bio}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="bg-gray-900 py-12">
      <div className="container mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-white font-bold text-xl">Alphalete Athletics</span>
            </div>
            <p className="text-gray-400 mb-4">
              Transform your body, transform your life. Join the Alphalete family today.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li><a href="#home" className="text-gray-400 hover:text-red-500 transition-colors">Home</a></li>
              <li><a href="#features" className="text-gray-400 hover:text-red-500 transition-colors">Features</a></li>
              <li><a href="#membership" className="text-gray-400 hover:text-red-500 transition-colors">Membership</a></li>
              <li><a href="#about" className="text-gray-400 hover:text-red-500 transition-colors">About</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-gray-400">
              <li>📍 123 Fitness Street, City</li>
              <li>📞 (555) 123-4567</li>
              <li>✉️ info@alphalete.com</li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-semibold mb-4">Hours</h4>
            <ul className="space-y-2 text-gray-400">
              <li>Mon-Fri: 5:00 AM - 11:00 PM</li>
              <li>Saturday: 6:00 AM - 10:00 PM</li>
              <li>Sunday: 7:00 AM - 9:00 PM</li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 text-center">
          <p className="text-gray-400">© 2025 Alphalete Athletics Club. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

// Login Modal Component
const LoginModal = ({ isOpen, onClose, onLogin, onSwitchToSignup }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock login - in real app this would make API call
    onLogin({
      name: 'John Doe',
      email: formData.email,
      membershipType: 'Monthly'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl p-8 w-full max-w-md mx-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
          <p className="text-gray-400">Sign in to your account</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-red-500 focus:outline-none"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-red-500 focus:outline-none"
            required
          />
          
          <button type="submit" className="w-full py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all">
            Sign In
          </button>
        </form>
        
        <div className="text-center mt-6">
          <p className="text-gray-400">
            Don't have an account?{' '}
            <button onClick={onSwitchToSignup} className="text-red-500 hover:underline">
              Sign up
            </button>
          </p>
        </div>
        
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl"
        >
          ×
        </button>
      </div>
    </div>
  );
};

// Signup Modal Component
const SignupModal = ({ isOpen, onClose, onSignup, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    membershipType: 'Monthly'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock signup - in real app this would make API call
    onSignup(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl p-8 w-full max-w-md mx-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">Join Alphalete</h2>
          <p className="text-gray-400">Start your fitness journey today</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-red-500 focus:outline-none"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-red-500 focus:outline-none"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-red-500 focus:outline-none"
            required
          />
          <select
            value={formData.membershipType}
            onChange={(e) => setFormData({...formData, membershipType: e.target.value})}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-red-500 focus:outline-none"
          >
            <option value="Student">Student - $29/month</option>
            <option value="Monthly">Monthly - $59/month</option>
            <option value="Custom">Custom - Contact us</option>
          </select>
          
          <button type="submit" className="w-full py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all">
            Join Now
          </button>
        </form>
        
        <div className="text-center mt-6">
          <p className="text-gray-400">
            Already have an account?{' '}
            <button onClick={onSwitchToLogin} className="text-red-500 hover:underline">
              Sign in
            </button>
          </p>
        </div>
        
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl"
        >
          ×
        </button>
      </div>
    </div>
  );
};

// Member Dashboard Component
const MemberDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const mockWorkouts = [
    { date: '2025-01-20', type: 'Strength Training', duration: '45 min' },
    { date: '2025-01-18', type: 'HIIT', duration: '30 min' },
    { date: '2025-01-15', type: 'Cardio', duration: '60 min' }
  ];

  const mockClasses = [
    { name: 'Morning HIIT', time: '7:00 AM', date: '2025-01-22', trainer: 'Sarah Chen' },
    { name: 'Strength Training', time: '6:00 PM', date: '2025-01-23', trainer: 'Alex Rodriguez' },
    { name: 'Yoga Flow', time: '8:00 AM', date: '2025-01-24', trainer: 'Marcus Johnson' }
  ];

  return (
    <div className="min-h-screen bg-black">
      {/* Dashboard Header */}
      <header className="bg-gray-900 border-b border-gray-700">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">A</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Member Dashboard</h1>
                <p className="text-gray-400">Welcome back, {user?.name}</p>
              </div>
            </div>
            <button 
              onClick={onLogout}
              className="px-4 py-2 text-white border border-red-500 rounded-lg hover:bg-red-500 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-2">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'workouts', label: 'My Workouts', icon: '💪' },
                { id: 'classes', label: 'Classes', icon: '📅' },
                { id: 'profile', label: 'Profile', icon: '👤' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === tab.id ? 'bg-red-500 text-white' : 'text-gray-400 hover:bg-gray-800'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold text-white">Overview</h2>
                
                {/* Stats Cards */}
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="bg-gray-900 rounded-xl p-6">
                    <h3 className="text-red-500 font-semibold mb-2">This Month</h3>
                    <p className="text-3xl font-bold text-white">12</p>
                    <p className="text-gray-400">Workouts Completed</p>
                  </div>
                  <div className="bg-gray-900 rounded-xl p-6">
                    <h3 className="text-red-500 font-semibold mb-2">Membership</h3>
                    <p className="text-3xl font-bold text-white">{user?.membershipType}</p>
                    <p className="text-gray-400">Active Plan</p>
                  </div>
                  <div className="bg-gray-900 rounded-xl p-6">
                    <h3 className="text-red-500 font-semibold mb-2">Next Class</h3>
                    <p className="text-xl font-bold text-white">Morning HIIT</p>
                    <p className="text-gray-400">Tomorrow 7:00 AM</p>
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-gray-900 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">Recent Workouts</h3>
                  <div className="space-y-3">
                    {mockWorkouts.slice(0, 3).map((workout, index) => (
                      <div key={index} className="flex items-center justify-between py-2 border-b border-gray-700">
                        <div>
                          <p className="text-white font-medium">{workout.type}</p>
                          <p className="text-gray-400 text-sm">{workout.date}</p>
                        </div>
                        <span className="text-red-500">{workout.duration}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'workouts' && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold text-white">My Workouts</h2>
                <div className="space-y-4">
                  {mockWorkouts.map((workout, index) => (
                    <div key={index} className="bg-gray-900 rounded-xl p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xl font-bold text-white">{workout.type}</h3>
                          <p className="text-gray-400">{workout.date}</p>
                        </div>
                        <span className="text-red-500 font-semibold">{workout.duration}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'classes' && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold text-white">Upcoming Classes</h2>
                <div className="space-y-4">
                  {mockClasses.map((cls, index) => (
                    <div key={index} className="bg-gray-900 rounded-xl p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xl font-bold text-white">{cls.name}</h3>
                          <p className="text-gray-400">{cls.date} at {cls.time}</p>
                          <p className="text-red-500">Trainer: {cls.trainer}</p>
                        </div>
                        <button className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                          Book
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'profile' && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold text-white">Profile</h2>
                <div className="bg-gray-900 rounded-xl p-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-gray-400 mb-2">Name</label>
                      <input 
                        type="text" 
                        value={user?.name || ''} 
                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-gray-400 mb-2">Email</label>
                      <input 
                        type="email" 
                        value={user?.email || ''} 
                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-gray-400 mb-2">Membership</label>
                      <input 
                        type="text" 
                        value={user?.membershipType || ''} 
                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-gray-400 mb-2">Member Since</label>
                      <input 
                        type="text" 
                        value="January 2025" 
                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                        readOnly
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const Components = {
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
};

export default Components;