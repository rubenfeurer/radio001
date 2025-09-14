# Radio Integration Plan

## Summary

**Goal**: Integrate the core radio functionality from the old radio project into the new WiFi-focused system, creating a unified Radio WiFi Configuration system that provides both reliable WiFi management and full internet radio capabilities.

**Current Architecture**:
- **New System**: Modern SvelteKit + FastAPI hybrid with reliable WiFi management
- **Old System**: Full-featured internet radio with hardware controls (WiFi components removed)
- **Target**: Combined system with the best of both worlds

## Current Folder Structure

```
radio001/                           # New WiFi system (active)
├── frontend/                       # SvelteKit frontend  
│   ├── src/routes/                 # WiFi setup pages
│   ├── src/lib/stores/wifi.ts      # WiFi state management
│   └── src/lib/components/         # WiFi UI components
├── backend/                        # FastAPI backend
│   └── main.py                     # WiFi API endpoints
└── compose/                        # Docker configuration

radio-old/                          # Old radio system (cleaned)
├── src/                           # Radio backend (WiFi removed)
│   ├── core/                      # Radio business logic
│   │   ├── radio_manager.py       # Central radio controller
│   │   ├── station_manager.py     # 3-slot station management
│   │   └── sound_manager.py       # System notifications
│   ├── hardware/                  # Physical controls
│   │   ├── audio_player.py        # MPV audio streaming
│   │   └── gpio_controller.py     # Buttons & rotary encoder
│   └── api/routes/                # Radio API endpoints
├── web/src/                       # Radio frontend components
│   └── lib/components/            # Radio UI (WiFi components removed)
└── sounds/                        # Notification audio files
```

## Quick Checklist

### Phase 1: Infrastructure ⏳
- [ ] Backend structure setup
- [ ] Dependencies integration
- [ ] Configuration extension
- [ ] Development environment

### Phase 2: Core Backend ⏳  
- [ ] Radio models & types
- [ ] Station management system
- [ ] Audio streaming system
- [ ] Sound notifications
- [ ] Central radio controller

### Phase 3: API Integration ⏳
- [ ] Radio API routes
- [ ] Station management endpoints
- [ ] System control endpoints  
- [ ] WebSocket integration

### Phase 4: Frontend Integration ⏳
- [ ] Type definitions
- [ ] Radio state store
- [ ] Core UI components
- [ ] Radio pages & routing

### Phase 5: Hardware Integration ⏳
- [ ] GPIO controller (mocked for dev)
- [ ] Hardware service integration
- [ ] Physical control events
- [ ] Button & encoder handling

### Phase 6: UI Integration ⏳
- [ ] Navigation enhancement
- [ ] Dashboard integration
- [ ] Mobile-responsive design
- [ ] Accessibility features

### Phase 7: Data & Storage ⏳
- [ ] Station database
- [ ] User preferences
- [ ] Sound assets
- [ ] Default content

### Phase 8: Development Tools ⏳
- [ ] Mock hardware mode
- [ ] Development API helpers
- [ ] Testing infrastructure
- [ ] Debug utilities

### Phase 9: Production Deployment ⏳
- [ ] Hardware dependencies
- [ ] System service integration
- [ ] Audio system setup
- [ ] Pi-specific configuration

### Phase 10: Integration Testing ⏳
- [ ] Cross-system integration
- [ ] Performance optimization
- [ ] User experience polish
- [ ] Final testing & deployment

---

## 🎯 Radio Integration Plan

### **Phase 1: Core Infrastructure Setup**
**Goal**: Establish the foundational components without breaking current WiFi functionality

#### **Step 1.1: Backend Structure Setup** 
- [ ] Create new backend modules in current project:
  ```
  backend/
  ├── core/
  │   ├── radio_manager.py
  │   ├── station_manager.py  
  │   ├── sound_manager.py
  │   └── models.py (radio models only)
  ├── hardware/
  │   ├── audio_player.py
  │   └── gpio_controller.py
  └── api/
      └── routes/
          ├── stations.py
          ├── radio.py
          └── websocket.py
  ```

#### **Step 1.2: Dependencies & Requirements**
- [ ] Update `backend/requirements.txt` with radio dependencies:
  ```python
  mpv==1.0.6          # Audio playback
  pigpio==1.78        # GPIO control (Pi only)
  python-mpv==1.0.6   # Python MPV bindings
  ```

#### **Step 1.3: Configuration Integration**
- [ ] Extend current `main.py` config with radio settings:
  ```python
  # Radio Settings (add to existing Config class)
  DEFAULT_VOLUME: int = 50
  MIN_VOLUME: int = 30
  MAX_VOLUME: int = 100
  NOTIFICATION_VOLUME: int = 40
  
  # Hardware Settings
  BUTTON_PIN_1: int = 17
  BUTTON_PIN_2: int = 16  
  BUTTON_PIN_3: int = 26
  ROTARY_CLK: int = 11
  ROTARY_DT: int = 9
  ROTARY_SW: int = 10
  ```

### **Phase 2: Core Radio Backend**
**Goal**: Implement radio functionality with mock hardware support for development

#### **Step 2.1: Models & Types**
- [ ] Create `backend/core/models.py` with radio models:
  ```python
  class RadioStation(BaseModel):
      name: str
      url: str
      slot: Optional[int] = None
      country: Optional[str] = None
      location: Optional[str] = None
  
  class SystemStatus(BaseModel):
      current_station: Optional[int] = None
      volume: int = 70
      is_playing: bool = False
      
  class VolumeUpdate(BaseModel):
      volume: int
  ```

#### **Step 2.2: Station Management** 
- [ ] Implement `backend/core/station_manager.py`:
  - 3-slot station storage system
  - JSON persistence (`data/stations.json`)
  - Default station loading
  - CRUD operations for stations

#### **Step 2.3: Audio System**
- [ ] Implement `backend/core/audio_player.py`:
  - MPV integration for streaming
  - Volume control
  - Play/stop/pause functionality
  - Mock mode for development (no actual audio)

#### **Step 2.4: Sound Notifications**
- [ ] Implement `backend/core/sound_manager.py`:
  - System event sounds (startup, errors)
  - Sound file management
  - Mock mode for development

#### **Step 2.5: Radio Manager (Core Controller)**
- [ ] Implement `backend/core/radio_manager.py`:
  - Central radio control logic
  - Station switching and playback
  - Volume management
  - Status broadcasting
  - Hardware integration hooks

### **Phase 3: API Integration**
**Goal**: Add radio API endpoints to existing FastAPI backend

#### **Step 3.1: Radio API Routes**
- [ ] Create `backend/radio_routes.py` and integrate into main API:
  ```python
  # Add to existing main.py
  from radio_routes import router as radio_router
  app.include_router(radio_router, prefix="/radio", tags=["radio"])
  ```

#### **Step 3.2: Station Management API**
- [ ] Implement station endpoints:
  ```python
  GET /radio/stations          # Get all stations
  GET /radio/stations/{slot}   # Get specific station  
  POST /radio/stations/{slot}  # Save station to slot
  POST /radio/stations/{slot}/toggle  # Play/stop station
  DELETE /radio/stations/{slot}  # Remove station
  ```

#### **Step 3.3: System Control API**
- [ ] Implement system endpoints:
  ```python
  GET /radio/status           # Get current status
  POST /radio/volume          # Set volume
  GET /radio/volume           # Get current volume
  POST /radio/stop            # Stop all playback
  ```

#### **Step 3.4: WebSocket Integration**
- [ ] Extend existing WebSocket handling:
  ```python
  # Add radio events to existing WebSocket
  - volume_update
  - station_change  
  - playback_status
  - system_status
  ```

### **Phase 4: Frontend Integration**  
**Goal**: Add radio UI components to existing SvelteKit frontend

#### **Step 4.1: Type Definitions**
- [ ] Extend `frontend/src/lib/types.ts`:
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
  }
  ```

#### **Step 4.2: Radio Store**
- [ ] Create `frontend/src/lib/stores/radio.ts`:
  - Station management state
  - Volume control state  
  - Playback status state
  - WebSocket integration for real-time updates

#### **Step 4.3: Core UI Components**
- [ ] Create `frontend/src/lib/components/radio/`:
  ```
  radio/
  ├── RadioStations.svelte    # 3-slot station interface
  ├── VolumeControl.svelte    # Volume slider
  ├── StationCard.svelte      # Individual station card
  └── PlaybackControls.svelte # Play/stop controls
  ```

#### **Step 4.4: Radio Pages**
- [ ] Create radio routes:
  ```
  frontend/src/routes/
  ├── radio/
  │   ├── +page.svelte        # Main radio interface
  │   └── stations/
  │       └── +page.svelte    # Station management
  ```

### **Phase 5: Hardware Integration**
**Goal**: Add physical control support (Pi only, mocked for development)

#### **Step 5.1: GPIO Controller**
- [ ] Implement `backend/hardware/gpio_controller.py`:
  - 3 physical buttons for stations
  - Rotary encoder for volume
  - Button press detection (short/long/triple)
  - Mock mode for development

#### **Step 5.2: Hardware Service Integration**  
- [ ] Add hardware initialization to main app:
  ```python
  # In main.py startup
  if not Config.IS_DEVELOPMENT:
      gpio_controller = GPIOController(
          button_callback=radio_manager.handle_button,
          volume_callback=radio_manager.handle_volume
      )
  ```

#### **Step 5.3: Physical Control Events**
- [ ] Implement hardware event handling:
  - Button 1/2/3: Toggle station slots
  - Rotary turn: Volume adjustment
  - Long press: System functions
  - Triple press: System reset

### **Phase 6: UI Integration & Navigation**
**Goal**: Seamlessly integrate radio UI into existing WiFi interface

#### **Step 6.1: Navigation Enhancement**
- [ ] Update main navigation to include radio:
  ```svelte
  <!-- Add to existing navigation -->
  <a href="/radio" class="nav-item">
      <RadioIcon />
      Radio
  </a>
  ```

#### **Step 6.2: Dashboard Integration**
- [ ] Add radio status to main dashboard:
  - Current playing station
  - Volume level
  - Quick play/stop controls

#### **Step 6.3: Mobile-First Design**
- [ ] Ensure radio UI works on mobile:
  - Touch-friendly controls
  - Responsive station cards
  - Accessible volume slider

### **Phase 7: Data & Storage**
**Goal**: Implement persistent storage and default content

#### **Step 7.1: Station Database**
- [ ] Create default station data:
  ```json
  // data/default_stations.json
  {
    "1": {"name": "Jazz FM", "url": "https://..."},
    "2": {"name": "Classical", "url": "https://..."},  
    "3": {"name": "Rock Radio", "url": "https://..."}
  }
  ```

#### **Step 7.2: User Preferences**
- [ ] Implement settings persistence:
  - Last volume level
  - Last played station
  - User customized stations

#### **Step 7.3: Sound Assets**
- [ ] Add notification sound files:
  ```
  assets/sounds/
  ├── startup.wav
  ├── success.wav
  └── error.wav
  ```

### **Phase 8: Testing & Development Tools**
**Goal**: Ensure reliable development and testing experience

#### **Step 8.1: Mock Hardware Mode**
- [ ] Implement comprehensive mocking:
  - Mock GPIO (no actual Pi hardware needed)
  - Mock audio (no actual sound output)  
  - Simulate button presses via API
  - Mock WebSocket events

#### **Step 8.2: Development API Endpoints**
- [ ] Add development helpers:
  ```python
  POST /dev/simulate-button/{button}  # Simulate hardware button
  POST /dev/simulate-volume/{change}  # Simulate volume knob
  GET /dev/hardware-status           # Mock hardware status
  ```

#### **Step 8.3: Testing Infrastructure** 
- [ ] Create test suites:
  - Station management tests
  - Audio system tests  
  - Hardware integration tests
  - WebSocket event tests

### **Phase 9: Production Deployment**
**Goal**: Deploy integrated system to Raspberry Pi

#### **Step 9.1: Hardware Dependencies**
- [ ] Update deployment scripts:
  ```bash
  # Add to setup scripts
  sudo apt-get install -y mpv libmpv-dev
  sudo pip install pigpio python-mpv
  sudo systemctl enable pigpiod
  ```

#### **Step 9.2: System Service Integration**
- [ ] Update systemd service to include hardware:
  ```ini
  [Unit]
  Description=Radio WiFi Service
  After=pigpiod.service
  Requires=pigpiod.service
  
  [Service]
  Environment=NODE_ENV=production
  Environment=MOCK_HARDWARE=false
  ```

#### **Step 9.3: Audio System Setup**
- [ ] Configure Pi audio system:
  - Audio device selection
  - Volume mixer setup  
  - Audio group permissions

### **Phase 10: Integration Testing & Polish**
**Goal**: Ensure seamless integration between WiFi and radio systems

#### **Step 10.1: Cross-System Integration**
- [ ] Test WiFi + Radio functionality:
  - Radio works in both AP and client modes
  - Network changes don't affect radio playback
  - Settings persist across WiFi changes

#### **Step 10.2: Performance Optimization**
- [ ] Optimize resource usage:
  - Efficient WebSocket updates
  - Minimal CPU usage for GPIO polling
  - Memory-efficient audio streaming

#### **Step 10.3: User Experience Polish**
- [ ] Final UX improvements:
  - Loading states for station changes
  - Error handling for network issues
  - Intuitive touch controls
  - Accessibility features

## 🔧 Development Strategy

1. **Mock-First Development**: Everything works without Pi hardware
2. **Incremental Integration**: Add one component at a time
3. **Preserve WiFi Functionality**: Never break existing WiFi features
4. **Test Early & Often**: Each phase includes testing
5. **Mobile-First UI**: Ensure great mobile experience

## 📁 Final Integrated Structure

```
radio001/                           # Unified Radio WiFi System
├── frontend/                       # SvelteKit frontend
│   ├── src/routes/
│   │   ├── wifi/                   # WiFi management (existing)
│   │   └── radio/                  # Radio interface (new)
│   ├── src/lib/stores/
│   │   ├── wifi.ts                 # WiFi state (existing)
│   │   └── radio.ts                # Radio state (new)
│   └── src/lib/components/
│       ├── wifi/                   # WiFi components (existing)
│       └── radio/                  # Radio components (new)
├── backend/                        # FastAPI backend
│   ├── main.py                     # Unified API server
│   ├── core/                       # Radio business logic (new)
│   └── hardware/                   # Physical controls (new)
├── data/                           # Persistent storage (new)
│   ├── stations.json               # User stations
│   └── preferences.json            # User settings
└── assets/sounds/                  # Notification audio (new)
```

## 🎯 Success Metrics

- [ ] **WiFi Functionality**: All existing WiFi features work unchanged
- [ ] **Radio Functionality**: 3-slot stations, volume control, hardware buttons
- [ ] **Cross-Platform**: Works on Mac (mocked) and Pi (hardware)
- [ ] **Mobile-First**: Excellent mobile web experience
- [ ] **Performance**: <2s station switching, minimal resource usage
- [ ] **Reliability**: Robust error handling, graceful degradation