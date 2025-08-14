import React from 'react';
import {
  // Navigation icons
  HomeIcon,
  UserGroupIcon,
  CreditCardIcon,
  CalendarIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  ChartBarIcon,
  UserIcon,
  ClipboardDocumentListIcon,
  BanknotesIcon,
  
  // Dashboard and stats icons
  CurrencyDollarIcon,
  UsersIcon,
  DocumentChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  
  // Action icons
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  ShareIcon,
  DocumentIcon,
  PhoneIcon,
  EnvelopeIcon,
  LockClosedIcon,
  
  // Status and misc icons
  ClockIcon,
  InformationCircleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  CloudArrowUpIcon,
  DevicePhoneMobileIcon,
  ChatBubbleLeftRightIcon,
  LinkIcon,
  DocumentTextIcon,
  AdjustmentsHorizontalIcon,
  BeakerIcon,
  CircleStackIcon,
  GemIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

import {
  HomeIcon as HomeSolid,
  UserGroupIcon as UserGroupSolid,
  CreditCardIcon as CreditCardSolid,
  CalendarIcon as CalendarSolid,
  Cog6ToothIcon as Cog6ToothSolid,
  ChartBarIcon as ChartBarSolid,
  UserIcon as UserSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListSolid,
  BanknotesIcon as BanknotesSolid,
  CheckCircleIcon as CheckCircleSolid,
  XCircleIcon as XCircleSolid,
  ExclamationTriangleIcon as ExclamationTriangleSolid
} from '@heroicons/react/24/solid';

// Icon mapping for easy replacement of emoji icons
export const iconMap = {
  // Navigation icons (emoji -> heroicon)
  '🏠': HomeIcon,
  '👥': UserGroupIcon,
  '💳': CreditCardIcon,
  '📅': CalendarIcon,
  '⚙️': Cog6ToothIcon,
  '☰': Bars3Icon,
  '✕': XMarkIcon,
  '📊': ChartBarIcon,
  '👤': UserIcon,
  '📋': ClipboardDocumentListIcon,
  '💰': BanknotesIcon,
  
  // Dashboard and stats icons
  '💱': CurrencyDollarIcon,
  '👨‍👩‍👧‍👦': UsersIcon,
  '📈': DocumentChartBarIcon,
  '⚠️': ExclamationTriangleIcon,
  '✓': CheckCircleIcon,
  '❌': XCircleIcon,
  
  // Action icons
  '➕': PlusIcon,
  '✏️': PencilIcon,
  '🗑️': TrashIcon,
  '👁️': EyeIcon,
  '📤': ShareIcon,
  '📄': DocumentIcon,
  '📱': PhoneIcon,
  '📩': EnvelopeIcon,
  '🔒': LockClosedIcon,
  
  // Status and misc icons
  '🕐': ClockIcon,
  '⏰': ClockIcon,
  'ℹ️': InformationCircleIcon,
  '→': ArrowRightIcon,
  '←': ArrowLeftIcon,
  '🔍': MagnifyingGlassIcon,
  '📂': DocumentTextIcon,
  '🔧': AdjustmentsHorizontalIcon,
  '🧪': BeakerIcon,
  '💾': CircleStackIcon,
  '🔗': LinkIcon,
  '💬': ChatBubbleLeftRightIcon,
  '📲': DevicePhoneMobileIcon,
  '☁️': CloudArrowUpIcon,
  '🎯': InformationCircleIcon, // Target -> Info as fallback
  '🏃‍♂️': UserIcon, // Runner -> User as fallback
  '💎': GemIcon, // Diamond for premium/all-time stats
  '✨': SparklesIcon // Sparkles for special effects
};

// Solid versions for active states
export const solidIconMap = {
  '🏠': HomeSolid,
  '👥': UserGroupSolid,
  '💳': CreditCardSolid,
  '📅': CalendarSolid,
  '⚙️': Cog6ToothSolid,
  '📊': ChartBarSolid,
  '👤': UserSolid,
  '📋': ClipboardDocumentListSolid,
  '💰': BanknotesSolid,
  '✓': CheckCircleSolid,
  '❌': XCircleSolid,
  '⚠️': ExclamationTriangleSolid,
};

// Reusable Icon component with consistent sizing and styling
export const Icon = ({ 
  name, 
  size = 'md', 
  solid = false, 
  className = '', 
  ...props 
}) => {
  const sizeMap = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8',
    '2xl': 'w-10 h-10'
  };

  const sizeClass = sizeMap[size] || sizeMap['md'];
  
  // Try to get icon from solid map first if solid=true, then fallback to outline
  const IconComponent = solid 
    ? (solidIconMap[name] || iconMap[name]) 
    : iconMap[name];

  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in iconMap`);
    return <span className={`inline-block ${sizeClass} ${className}`} {...props}>{name}</span>;
  }

  return (
    <IconComponent 
      className={`${sizeClass} ${className}`} 
      {...props} 
    />
  );
};

// Specific navigation icons with consistent styling
export const NavigationIcon = ({ name, isActive = false, size = 'lg' }) => (
  <Icon 
    name={name} 
    solid={isActive} 
    size={size}
    className={`transition-all duration-200 ${isActive ? 'text-primary-600' : 'text-gray-500'}`}
  />
);

// Dashboard stat icons with specific styling
export const StatIcon = ({ name, color = 'primary', size = '2xl' }) => {
  const colorMap = {
    primary: 'text-primary-500',
    success: 'text-success-500', 
    warning: 'text-warning-500',
    danger: 'text-danger-500',
    info: 'text-info-500'
  };
  
  return (
    <Icon 
      name={name} 
      size={size}
      className={`${colorMap[color] || colorMap.primary}`}
    />
  );
};

// Action button icons
export const ActionIcon = ({ name, size = 'sm', className = '' }) => (
  <Icon 
    name={name} 
    size={size}
    className={`${className}`}
  />
);

export default Icon;