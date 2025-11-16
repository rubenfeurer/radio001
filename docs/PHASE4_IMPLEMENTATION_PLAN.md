# Phase 4: Frontend Integration Implementation Plan

**Document Version**: 1.0  
**Created**: December 2024  
**Status**: Ready for Implementation  
**Priority**: High - Next Phase  

## 🎯 Overview

Phase 4 focuses on implementing the frontend radio interface to complete the unified WiFi + Radio system. This phase will add radio UI components, state management, and real-time WebSocket integration to the existing SvelteKit frontend.

## 📋 Current State Analysis

### ✅ **What's Ready**
- **Backend Radio API**: Fully functional `/radio/*` endpoints
- **WebSocket Integration**: Real-time radio updates available
- **3-Slot Station System**: Backend supports volume control and station management  
- **WiFi Frontend**: Working SvelteKit app with WiFi components and store
- **Infrastructure**: Docker setup, CI/CD pipeline, comprehensive testing

### 🔄 **What's Missing**
- Radio state management (Svelte stores)
- Radio UI components (station cards, volume controls)
- `/radio` route and pages
- Dashboard integration showing radio status
- WebSocket connection for live updates

## 🚀 Implementation Steps

### **Step 1: Extend Type Definitions**
**⏱️ Estimated Time**: 15 minutes  
**Priority**: High  
**Dependencies**: None

**Tasks:**
- [ ] Extend `frontend/src/lib/types.ts` with radio interfaces
- [ ] Add `RadioStation`, `RadioStatus`, `StationsResponse` types
- [ ] Add WebSocket message types for real-time updates

**Files to Modify:**
```
frontend/src/lib/types.ts
```

**New Interfaces:**
```typescript
export interface RadioStation {
    name: string;
    url: string;
    slot: number;
    country?: string;
    location?: string;
}

export interface RadioStatus {
    current_station: number | null;
    volume: number;
    is_playing: boolean;
    playback_state: 'stopped' | 'playing' | 'paused' | 'buffering' | 'error';
    current_station_info?: RadioStation | null;
}

export interface StationsResponse {
    stations: { [key: number]: RadioStation | null };
    total_configured: number;
}

export interface WSRadioMessage {
    type: 'station_change' | 'volume_change' | 'playback_state' | 'error';
    data: any;
    timestamp: number;
}
```

---

### **Step 2: Create Radio Store**
**⏱️ Estimated Time**: 45 minutes  
**Priority**: High  
**Dependencies**: Step 1 completed

**Tasks:**
- [ ] Create `frontend/src/lib/stores/radio.ts`
- [ ] Implement reactive state stores (stations, radioStatus, loading, errors)
- [ ] Add WebSocket connection and message handling
- [ ] Implement API functions (loadStations, saveStation, toggleStation, setVolume)
- [ ] Add derived stores for computed values

**Files to Create:**
```
frontend/src/lib/stores/radio.ts
```

**Key Features:**
- Station management state (3-slot system)
- Volume control state with hardware limits
- Playback status with real-time updates
- WebSocket integration for live data
- Error handling and loading states
- API integration for all radio endpoints

---

### **Step 3: Create Radio UI Components**
**⏱️ Estimated Time**: 1.5 hours  
**Priority**: High  
**Dependencies**: Step 2 completed

**Tasks:**
- [ ] Create component directory structure
- [ ] Build `StationCard.svelte` for individual station display
- [ ] Build `VolumeControl.svelte` with slider and buttons
- [ ] Build `RadioStations.svelte` as main container component
- [ ] Add responsive design and dark mode support

**Files to Create:**
```
frontend/src/lib/components/radio/StationCard.svelte
frontend/src/lib/components/radio/VolumeControl.svelte  
frontend/src/lib/components/radio/RadioStations.svelte
```

**Component Features:**
- **StationCard**: Play/stop buttons, station info, edit functionality
- **VolumeControl**: Range slider, +/- buttons, volume indicators
- **RadioStations**: Grid layout, real-time status, empty states

---

### **Step 4: Create Radio Pages**
**⏱️ Estimated Time**: 45 minutes  
**Priority**: High  
**Dependencies**: Step 3 completed

**Tasks:**
- [ ] Create `/radio` route structure
- [ ] Build main radio page (`/radio/+page.svelte`)
- [ ] Add "Now Playing" section with live status
- [ ] Integrate volume control and station management
- [ ] Add navigation links to other sections

**Files to Create:**
```
frontend/src/routes/radio/+page.svelte
frontend/src/routes/radio/stations/+page.svelte (future)
```

**Page Features:**
- Real-time "Now Playing" display
- Integrated volume control
- 3-slot station interface
- WebSocket connection status
- Navigation to other app sections

---

### **Step 5: Update Main Dashboard**
**⏱️ Estimated Time**: 30 minutes  
**Priority**: Medium  
**Dependencies**: Step 4 completed

**Tasks:**
- [ ] Add radio status card to main dashboard (`/+page.svelte`)
- [ ] Show current playing station and volume
- [ ] Add quick navigation to radio section
- [ ] Update header with radio connectivity status

**Files to Modify:**
```
frontend/src/routes/+page.svelte
```

**Dashboard Features:**
- Radio status card alongside WiFi status
- Quick play/stop controls
- Current station display
- Volume level indicator

---

### **Step 6: Add Navigation Integration**
**⏱️ Estimated Time**: 20 minutes  
**Priority**: Medium  
**Dependencies**: Step 5 completed

**Tasks:**
- [ ] Add radio navigation button to main dashboard
- [ ] Update page titles and meta tags
- [ ] Add radio icon to header when on radio pages
- [ ] Ensure consistent navigation flow

**Files to Modify:**
```
frontend/src/routes/+page.svelte
frontend/src/routes/+layout.svelte (if needed)
```

---

### **Step 7: Testing and Polish**
**⏱️ Estimated Time**: 45 minutes  
**Priority**: Medium  
**Dependencies**: Step 6 completed

**Tasks:**
- [ ] Test WebSocket connectivity and reconnection
- [ ] Verify responsive design on mobile devices  
- [ ] Test dark mode compatibility
- [ ] Verify error handling and loading states
- [ ] Test integration with backend API

**Testing Checklist:**
- [ ] Station loading and display
- [ ] Play/stop functionality
- [ ] Volume control with hardware limits
- [ ] WebSocket real-time updates
- [ ] Error handling and recovery
- [ ] Mobile responsiveness
- [ ] Dark mode support

## 📁 File Structure After Implementation

```
frontend/src/
├── lib/
│   ├── components/
│   │   ├── radio/
│   │   │   ├── StationCard.svelte      # Individual station display
│   │   │   ├── VolumeControl.svelte    # Volume slider and controls
│   │   │   └── RadioStations.svelte    # Main stations container
│   │   └── SignalStrength.svelte       # Existing WiFi component
│   ├── stores/
│   │   ├── radio.ts                    # Radio state management
│   │   └── wifi.ts                     # Existing WiFi store
│   └── types.ts                        # Extended with radio types
├── routes/
│   ├── radio/
│   │   └── +page.svelte               # Main radio interface
│   ├── +layout.svelte                 # App layout
│   └── +page.svelte                   # Updated dashboard
```

## 🔌 API Integration Points

### **Radio Endpoints Used:**
- `GET /radio/status` - System status for dashboard
- `GET /radio/stations` - Load all configured stations
- `POST /radio/stations/{slot}` - Save station to slot
- `POST /radio/stations/{slot}/toggle` - Play/stop station  
- `POST /radio/volume` - Set volume level
- `POST /radio/stop` - Stop all playback
- `WS /ws/radio` - Real-time updates

### **WebSocket Messages:**
- `station_change` - Station switched or stopped
- `volume_change` - Volume level updated  
- `playback_state` - Playing/stopped/buffering status
- `error` - System or playback errors

## 🎨 Design Guidelines

### **Visual Design:**
- **Consistent with WiFi UI**: Match existing card layouts and button styles
- **Mobile-First**: Optimized for 320px+ screens
- **Dark Mode**: Full support with proper contrast ratios
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### **Component Patterns:**
- **Cards**: Use existing `.card` CSS class for consistency
- **Buttons**: Follow `.btn-primary` and `.btn-secondary` patterns  
- **Loading States**: Skeleton loading and spinners
- **Error States**: Red alert boxes matching WiFi error patterns

### **Responsive Breakpoints:**
- **Mobile**: 320px - 768px (primary target)
- **Tablet**: 768px - 1024px (secondary)
- **Desktop**: 1024px+ (tertiary)

## ⚡ Performance Considerations

### **WebSocket Management:**
- Auto-reconnect on connection loss
- Graceful fallback when WebSocket unavailable
- Cleanup connections on page unload

### **State Management:**
- Minimize API calls with smart caching
- Debounce volume control updates
- Lazy load station metadata when needed

### **Bundle Size:**
- Reuse existing Tailwind classes
- Share common utilities with WiFi components
- Tree-shake unused radio features

## 🧪 Testing Strategy

### **Manual Testing:**
1. **Station Management**: Add, edit, delete stations in all slots
2. **Playback Control**: Play, stop, switch between stations
3. **Volume Control**: Slider, buttons, hardware limits
4. **Real-time Updates**: WebSocket connection and message handling
5. **Error Handling**: Network failures, invalid stations, API errors
6. **Responsive Design**: Mobile, tablet, desktop layouts
7. **Dark Mode**: All components in light/dark themes

### **Integration Testing:**
- Backend API compatibility
- WebSocket message format validation
- Error response handling
- Loading state management

## 🚀 Deployment Notes

### **Development Mode:**
- WebSocket connects to `ws://localhost:8000/ws/radio`
- API calls proxied to backend container
- Hot reload for component changes

### **Production Mode:**
- WebSocket uses secure connection (wss://) if HTTPS
- Static frontend served by nginx
- API calls to Docker backend container

## 📊 Success Metrics

### **Completion Criteria:**
- [ ] All 7 implementation steps completed
- [ ] Manual testing checklist passed
- [ ] WebSocket connectivity working
- [ ] Mobile responsiveness verified
- [ ] Dark mode support confirmed
- [ ] Error handling tested
- [ ] Performance acceptable (< 3s initial load)

### **User Experience Goals:**
- **Intuitive Interface**: Clear station management and playback controls
- **Real-time Feedback**: Immediate visual feedback for all actions
- **Mobile Optimized**: Smooth experience on phone screens
- **Reliable**: Graceful handling of network issues and errors

## 🔄 Next Steps After Phase 4

### **Phase 5: Enhanced Features**
- Station editing modal with URL validation
- Station search and discovery
- Favorites and history
- Audio visualization
- Hardware button simulation for development

### **Phase 6: Advanced Integration**  
- Custom station artwork
- Streaming metadata display
- Multi-room audio support
- Advanced volume controls (bass, treble)

---

## 📞 Support and Resources

### **Documentation References:**
- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [Tailwind CSS Components](https://tailwindcss.com/docs)
- [WebSocket API Reference](../backend/api/routes/websocket.py)
- [Radio API Reference](../backend/api/routes/radio.py)

### **Development Commands:**
```bash
# Start development environment
docker-compose -f compose/docker-compose.yml up radio-backend -d
cd frontend && npm run dev

# Test radio endpoints
curl http://localhost:8000/radio/status
curl http://localhost:8000/radio/stations

# WebSocket testing
wscat -c ws://localhost:8000/ws/radio
```

---

**📝 Document Maintenance:**
- Update completion status as steps are implemented
- Add actual implementation notes and lessons learned
- Track any deviations from the original plan
- Update time estimates based on actual implementation time

---

*Last Updated: December 2024*  
*Implementation Status: ⏳ Ready to Start*