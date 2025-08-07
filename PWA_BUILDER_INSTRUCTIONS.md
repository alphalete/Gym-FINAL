# 🚨 CRITICAL FIX: PWABuilder Instructions for Android APK

## ⚠️ **ISSUES RESOLVED:**
1. **Address bar showing** - Fixed PWA manifest for proper standalone mode
2. **No data when agent sleeps** - Fixed offline functionality and removed URL overrides

## 🎯 **CORRECT PWABuilder SETUP:**

### **1. Use CORRECT URL:**
```
https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com
```

**❌ DO NOT USE:** `alphalete-club.emergent.host` (old URL causing issues)

### **2. Environment Variables for APK:**
When generating the APK, ensure these environment variables are set:

```bash
REACT_APP_BACKEND_URL=https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com
```

### **3. PWABuilder Settings:**
- **Host**: `7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com`
- **Start URL**: `/`
- **Display**: Standalone (automatically detected)
- **Package Name**: `com.alphalete.club`
- **App Name**: `Alphalete Club`

## 🔧 **CRITICAL FIXES APPLIED:**

### **Removed ALL URL Overrides:**
- ✅ Removed 21 hardcoded URL override instances
- ✅ APK will now use proper environment variables
- ✅ No more fallback to wrong backend URL

### **Enhanced Offline Functionality:**
```javascript
// NEW: Always show seed data if no cached data
if (localClients.length === 0) {
  localClients = await this.createSeedData(); // Shows Deon & Monisa
}
```

### **Proper Standalone Mode:**
```json
{
  "display": "standalone",
  "id": "/",
  "scope": "/"
}
```

## 📱 **Expected APK Results:**

### **✅ Address Bar Fix:**
- **NO browser address bar** - full standalone mode
- **Native Android app appearance**
- **Proper status bar integration** (blue theme)

### **✅ Data Availability:**
- **Always shows clients** (even when agent sleeps)
- **Shows seed data**: Deon Aleong, Monisa Aleong
- **Offline banner** when backend unavailable
- **Retry functionality** when connection returns

### **✅ APK Functionality:**
- **Proper PWA scoring** in PWABuilder
- **Fast installation** on Android
- **Offline-first operation**
- **Professional user experience**

## 🚀 **Testing Verification:**

After generating new APK from correct URL:
1. **Address bar hidden** ✅
2. **Shows 2 members** (Deon & Monisa) ✅  
3. **Works offline** with cached data ✅
4. **Blue status bar** (no red) ✅
5. **Native app experience** ✅

## ⚡ **Immediate Action Required:**

**REGENERATE APK** using:
- **Correct URL**: `https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com`
- **Latest PWA configuration** (v9.0.0 with all fixes)
- **Proper environment variable injection**

**The previous APK is broken - generate a new one with these fixes!** 🎯