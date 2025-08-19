# Alphalete Club PWA

A modern Progressive Web Application for gym membership management with offline-first capabilities and Google Sheets integration.

## 🚀 Features

- **Offline-First Architecture**: Full functionality without internet connection
- **Google Sheets Integration**: Real-time sync with Google Sheets as backend
- **Member Management**: Add, edit, delete, and manage gym members
- **Payment Tracking**: Record payments and track billing cycles
- **Email & WhatsApp Integration**: Send reminders and receipts
- **30-Day Billing Logic**: Automatic due date calculation
- **Progressive Web App**: Install on mobile devices like a native app

## ⚙️ Setup Instructions

### Prerequisites

1. Node.js (v14 or higher)
2. Yarn package manager
3. Google Apps Script Web App (for backend)

### Google Sheets Setup

1. **Create a new Google Sheet** with two sheets:
   - `Members` sheet with columns: id, name, email, phone, join_date, monthly_fee, status, next_payment_date, updatedAt
   - `Payments` sheet with columns: id, memberId, amount, date, createdAt, updatedAt

2. **Create Google Apps Script**:
   - Go to script.google.com
   - Create a new project
   - Set up Web App endpoints for CRUD operations
   - Deploy as Web App with execute permissions for "Anyone"

3. **Get your credentials**:
   - Copy the Web App URL (ends with `/exec`)
   - Generate an API key for authentication

### Environment Configuration

Create `/frontend/.env` file:

```env
REACT_APP_SHEETS_API_URL=<YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL>
REACT_APP_SHEETS_API_KEY=<YOUR_API_KEY>
WDS_SOCKET_PORT=443
```

**Important**: Replace the placeholder values with your actual Google Apps Script URL and API key.

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd alphalete-club-pwa
   ```

2. **Install dependencies**
   ```bash
   cd frontend
   yarn install
   ```

3. **Start development server**
   ```bash
   yarn start
   ```

4. **Build for production**
   ```bash
   yarn build
   ```

## 📱 Mobile App (Optional)

### Android with Capacitor

1. **Install Capacitor**
   ```bash
   yarn add @capacitor/core @capacitor/cli
   yarn add @capacitor/android
   ```

2. **Initialize Capacitor**
   ```bash
   npx cap init
   ```

3. **Build and sync**
   ```bash
   yarn build
   npx cap add android
   npx cap sync
   ```

4. **Open in Android Studio**
   ```bash
   npx cap open android
   ```

## 🔧 Configuration

### Billing Settings

The app uses a 30-day billing cycle by default:
- First due date = join date + 30 days
- First payment within cycle doesn't change due date
- Multiple payments in same cycle extend due date by +30 days

### Email Templates

Configure email templates in Settings:
- Payment Reminder template
- Payment Receipt template
- Use variables: `{memberName}`, `{dueDate}`, `{amount}`

### Sync Behavior

- **Auto-sync**: Happens on app start and when coming back online
- **Manual sync**: Available in Settings page
- **Offline capability**: All operations work offline and sync when online

## 🏗️ Architecture

### Frontend
- **React** with hooks and functional components
- **Tailwind CSS** for styling
- **IndexedDB** for offline data storage
- **Service Worker** for PWA capabilities

### Backend Integration
- **Google Sheets API** via Apps Script
- **Offline-first** with local storage fallback
- **Auto-sync** capabilities

### Key Components
- `src/lib/sheetsApi.js` - Google Sheets API client
- `src/lib/sync.js` - Offline sync management
- `src/lib/billing.js` - 30-day billing logic
- `src/data/members.repo.js` - Member data repository

## 🔄 Sync Process

1. **Online**: Operations go to Google Sheets immediately
2. **Offline**: Operations stored locally with `pending: 1` flag
3. **Back online**: Auto-sync pushes pending changes to Google Sheets
4. **Manual sync**: Available via Settings > Sync Now button

## 🛠️ Development

### Testing Offline Functionality

1. Turn off internet connection
2. Add/edit/delete members → should work locally
3. Turn internet back on
4. Check Google Sheets → changes should sync automatically

### Adding New Features

1. Update repository pattern in `src/data/members.repo.js`
2. Add Sheets API endpoints in `src/lib/sheetsApi.js`
3. Update sync logic in `src/lib/sync.js` if needed

## 📧 Email & WhatsApp Integration

- **Email**: Uses `mailto:` links with template system
- **WhatsApp**: Direct links to WhatsApp with pre-filled messages
- **Templates**: Configurable in Settings with variable substitution

## 🚀 Deployment

1. **Build production version**
   ```bash
   yarn build
   ```

2. **Deploy to hosting service** (Netlify, Vercel, etc.)
   - Upload `build` folder contents
   - Set environment variables in hosting service

3. **PWA Installation**
   - Users can install from browser
   - Works offline after installation
   - Auto-updates when new version available

## 🔐 Security

- API keys stored in environment variables
- No sensitive data in code repository
- Google Apps Script handles authentication
- Local data encrypted in IndexedDB

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

For questions or support, please open an issue in the repository.
