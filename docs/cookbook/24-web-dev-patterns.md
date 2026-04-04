## Web Development Patterns

### Data Injection Pattern (Jinja2 → External JS)

**Source:** `PDF2Calendar/01_Project/templates/stats.html` + `static/js/stats.js`

When server-rendered templates have inline JavaScript with Jinja2 expressions, you can't simply move the JS to an external file. Use a data injection pattern:

**Template (stats.html):**
```html
<!-- Small inline script injects server-rendered data -->
<script>
    window.STATS_DATA = {
        dailyVisits: {{ daily_visits | tojson }},
        deviceData: {{ stats.page_visits.by_device | tojson }},
        exportDownload: {{ stats.export_download.by_parser | tojson }},
        // ... other server data
    };
</script>
<!-- Main logic in external file -->
<script src="/static/js/stats.js"></script>
```

**External JS (stats.js):**
```javascript
// Access server data via global object
const dailyData = window.STATS_DATA.dailyVisits;
const deviceData = window.STATS_DATA.deviceData;

// Use data in charts, etc.
new Chart(ctx, {
    data: { labels: dailyData.map(d => d[0]) }
});
```

**Benefits:**
- Separates data (server) from logic (client)
- External JS is cacheable
- ~90% of code moves to external file
- Only 10-20 lines of data assignment stays inline

**Best for:** Flask/Django/Jinja2 templates with significant inline JavaScript.

---

### Wave-Based Parallel Execution

**Source:** PDF2Calendar refactor session (2026-02-09)

Pattern for orchestrating multiple parallel tasks with fresh context per task:

**PLAN.md structure:**
```markdown
### Wave 1 (parallel - no dependencies)
- [ ] Task 1.1: Create file A
- [ ] Task 1.2: Create file B
- [ ] Task 1.3: Modify file C

### Wave 2 (depends on Wave 1)
- [ ] Task 2.1: Use files from Wave 1

### Wave 3 (verification)
- [ ] Task 3.1: Run tests
```

**Execution pattern (Claude Code):**
```javascript
// Wave 1: Spawn parallel tasks
Task(subagent_type="developer", prompt="Task 1.1: ...")
Task(subagent_type="developer", prompt="Task 1.2: ...")
Task(subagent_type="developer", prompt="Task 1.3: ...")

// Wait for all Wave 1 to complete
// Commit: git commit -m "feat(wave-1): description"
// Update PLAN.md checkboxes to [x]

// Wave 2: Sequential or parallel based on dependencies
Task(subagent_type="developer", prompt="Task 2.1: ...")
```

**Key principles:**
1. **Fresh context per task** - Each subagent starts clean, no conversation history
2. **Atomic commits** - One wave = one commit (easy rollback)
3. **State in files** - PLAN.md is source of truth, not conversation
4. **Orchestrator stays light** - Delegate heavy work to subagents

**Best for:** Multi-file refactors, feature implementations, any work that can be parallelized.

---

### ES Module Dependency Injection

**Source:** `PDF2Calendar/01_Project/static/js/modules/feedback.js`

When extracting JS code to ES modules, you often need access to objects from the main file (state machines, loggers, etc.). Passing direct references creates circular imports. Use callback injection:

**Module (feedback.js):**
```javascript
// Dependencies injected at init time (not imported)
let getWizardState = () => ({ currentStep: 1 });
let getSessionLog = () => ({ toArray: () => [], info: () => {} });

export const FeedbackModal = {
    init(options = {}) {
        // Accept getters instead of direct references
        if (options.getWizardState) getWizardState = options.getWizardState;
        if (options.getSessionLog) getSessionLog = options.getSessionLog;
        // ... rest of init
    },

    open() {
        const state = getWizardState();  // Call getter when needed
        const log = getSessionLog();
        log.info?.(`Feedback opened (Step ${state?.currentStep})`);
    }
};
```

**Main file (main.js):**
```javascript
import { FeedbackModal } from './modules/feedback.js';

// Inject dependencies with getters
FeedbackModal.init({
    getWizardState: () => Wizard.state,
    getSessionLog: () => SessionLog
});
```

**Benefits:**
- No circular imports (module doesn't import main)
- Module is testable (can mock dependencies)
- Lazy evaluation (gets current state, not stale reference)
- Default fallbacks for standalone usage

**Best for:** Extracting modals, widgets, or components that need access to main app state.

---

### Shared State Module Pattern

**Source:** `PDF2Calendar/01_Project/static/js/modules/state.js`

When a vanilla JS app has a state machine that multiple modules need to access, extract it to a shared module. This eliminates duplicate state and enables further modularization.

**State module (state.js):**
```javascript
// Shared state that other modules can import
export const state = {
    currentStep: 1,
    schedules: [],
    employees: [],
    dateRange: { start: null, end: null },
    selectedEmployee: null
};

// State manipulation functions
export function goToStep(step, skipAnimation = false) {
    if (step < 1 || step > 4) return false;
    if (step > state.maxUnlockedStep) return false;
    state.currentStep = step;
    updateUI();
    return true;
}

export function resetState() {
    Object.assign(state, {
        currentStep: 1,
        schedules: [],
        employees: [],
        // ... reset to defaults
    });
}

export function initWizard() {
    cacheElements();
    bindStepEvents();
    updateUI();
}
```

**Main file (main.js):**
```javascript
// Import state and functions (no duplicate definition needed)
import {
    state,
    goToStep,
    completeStep,
    setCardState,
    resetState,
    initWizard
} from './modules/state.js';

// Use directly
state.schedules = data.schedules;
completeStep(2);
goToStep(3);
```

**Other modules can now access state:**
```javascript
// calendar.js
import { state } from './state.js';

export function renderCalendar() {
    const schedules = state.schedules;  // Direct access!
    const dateRange = state.dateRange;
    // ... render logic
}
```

**Migration steps:**
1. Create state module with exported state object + functions
2. Add imports to main.js
3. Find/replace: `Wizard.state.` → `state.`, `Wizard.goToStep` → `goToStep`, etc.
4. Delete the original state machine object

**Benefits:**
- Eliminates duplicate state management code
- Enables further module extraction (views, utils can import state)
- Single source of truth for application state
- Cleaner main file (removed ~260 lines in PDF2Calendar)

**Best for:** Vanilla JS apps with state machines that have grown large (500+ lines).

---

