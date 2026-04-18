# ADRminer Streamlit UI - User Experience Design

**Version:** 1.0  
**Date:** 2026-04-17  
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#1-overview)
2. [User Flows](#2-user-flows)
3. [Screen Designs](#3-screen-designs)
4. [Interactive Components](#4-interactive-components)
5. [Filtering and Search](#5-filtering-and-search)
6. [Export Options](#6-export-options)
7. [Responsive Design](#7-responsive-design)
8. [Theme and Customization](#8-theme-and-customization)
9. [Performance Optimizations](#9-performance-optimizations)

---

## 1. Overview

### 1.1 Main Interface Layout

The Streamlit UI features a **sidebar-based navigation** with a clean, modern interface:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ADRminer 🏗️                                      ☰ Theme Settings │
├─────────────────────────────────────────────────────────────────────┤
│ ▸ Home              │                                          │
│ ▸ Analyze ADRs      │                                          │
│ ▸ Dashboard          │                                          │
│ ▸ Compare ADRs       │                                          │
│ ▸ Settings           │                                          │
├───────────────────────┼──────────────────────────────────────────┤
│                      │                                          │
│   Navigation Panel   │           Main Content Area               │
│   (Sidebar)         │                                          │
│                      │                                          │
│                      │                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Principles

- **Actionability First**: Insights and recommendations are prominently displayed
- **Progressive Disclosure**: Show overview first, details on demand
- **Visual Feedback**: Progress bars, status indicators, and real-time updates
- **Consistent Patterns**: Similar interactions across all screens
- **Mobile-First**: Responsive design that works on all screen sizes

---

## 2. User Flows

### 2.1 Flow 1: Quick Analysis (Most Common)

**Goal:** User wants to quickly analyze a folder of ADRs and get insights

**Steps:**
1. User opens Streamlit app → Home page
2. Clicks "Analyze ADRs" in sidebar
3. Uploads folder or selects directory
4. Selects services to run (checkboxes):
   - ☑ Topic Mining
   - ☑ Classification (selects framework: Kruchten)
   - ☑ ADR Checking
5. Clicks "Start Analysis"
6. Sees progress bar with real-time updates
7. Redirects to Results page with insights highlighted

**Time to first insight:** ~30 seconds (for 10 ADRs)

---

### 2.2 Flow 2: Single ADR Deep Dive

**Goal:** User wants to understand a specific ADR in detail

**Steps:**
1. Navigates to "Analyze ADRs"
2. Selects "Single ADR" mode
3. Pastes ADR text or uploads file
4. Selects analysis options
5. Clicks "Analyze"
6. Sees detailed results with:
   - Topic probabilities (bar chart)
   - Classification with alternatives
   - Section-by-section quality check
   - Actionable recommendations
7. Can click "Compare with similar ADRs" to see patterns

---

### 2.3 Flow 3: Dashboard Exploration

**Goal:** User wants to explore insights across their ADR collection

**Steps:**
1. Navigates to "Dashboard" (available after first analysis)
2. Sees overview cards:
   - 📊 Total ADRs: 25
   - 🎯 Quality Score: 0.72
   - 🔥 Topics: 8
   - ⚠️ Last Analysis: 2 hours ago
3. Scrolls to sections:
   - **Topic Distribution** (pie chart)
   - **Classification Balance** (bar chart)
   - **Quality Trends** (line chart over time)
   - **Top Insights** (priority badges)
4. Clicks on insight → Shows affected ADRs
5. Clicks on ADR → Shows detailed view

---

### 2.4 Flow 4: ADR Comparison

**Goal:** User wants to compare multiple ADRs

**Steps:**
1. Navigates to "Compare ADRs"
2. Selects 2-5 ADRs from dropdown
3. Chooses comparison dimensions:
   - Topics
   - Classification
   - Template adherence
   - All of the above
4. Sees comparison matrix with:
   - Similarity scores
   - Differences highlighted
   - Visual comparison charts
5. Can export comparison as PDF

---

## 3. Screen Designs

### 3.1 Screen 1: Home Page

```
┌─────────────────────────────────────────────────────────────────────┐
│  🏗️ ADRminer - Analyze Your Architectural Decisions            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Welcome! ADRminer helps you analyze, improve, and understand   │
│  your Architectural Decision Records (ADRs).                        │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  📊 Topics   │  │  🎯 Classify  │  │  ✅  Check    │      │
│  │  Discover   │  │  Categorize  │  │  Quality     │      │
│  │  what      │  │  decisions   │  │  and         │      │
│  │  matters   │  │  by type     │  │  compliance  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📁 Quick Start: Analyze Your First ADRs              │   │
│  │                                                      │   │
│  │  [Upload Folder] [Browse...]                     │   │
│  │                                                      │   │
│  │  ☑ Topic Mining     ☑ Classification ☑ Checking │   │
│  │  ☑ Generate Insights                                │   │
│  │                                                      │   │
│  │  [Start Analysis →]                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📚 Recent Analyses                                    │   │
│  │                                                      │   │
│  │  • my-project (25 ADRs) - 2 hours ago               │   │
│  │  • frontend-team (12 ADRs) - 1 day ago               │   │
│  │  • backend-service (18 ADRs) - 3 days ago             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Screen 2: Analyze ADRs

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Analyze ADRs                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: Select Input                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  ◉ Single ADR                                                │   │
│    [Paste text here...]                                     │   │
│    or [Upload ADR file...]                                   │   │
│                                                              │   │
│  ○ Folder of ADRs                                           │   │
│    [Select folder: /path/to/adrs]                           │   │
│    Found: 25 ADR files                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Step 2: Choose Services                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  ☑ Topic Mining                                             │   │
│    Model: [Pre-trained v1.0 ▼]                              │   │
│    Topics: [Auto ▼]                                         │   │
│                                                              │   │
│  ☑ Classification                                           │   │
│    Framework: [Kruchten ▼] (Quality Attributes, Zimmermann)│   │
│    Examples: [Built-in ▼] (None, Custom, Built-in)        │   │
│                                                              │   │
│  ☑ ADR Checking                                            │   │
│    Template: [MADR ▼]                                      │   │
│                                                              │   │
│  ☑ Generate Insights (Quality, Patterns, Recommendations)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Step 3: Output Options                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  ☑ Save metadata as JSON sidecar files                    │   │
│  ☑ Generate Markdown report                              │   │
│  ☑ Create dashboard                                      │   │
│  Output folder: [Same as input ▼]                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│                     [Start Analysis →]                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Screen 3: Progress View

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⏳ Processing ADRs...                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Overall Progress: ████████████░░░░░░░░░░ 60%                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ✅ Topic Mining (25/25) - 45 seconds                    │   │
│  │                                                         │   │
│  │ ⏳ Classification (15/25) - 2:15 elapsed                 │   │
│  │    ███████████████░░░░░░░░░░░░░░ 60%               │   │
│  │                                                         │   │
│  │ ⏸ ADR Checking (0/25) - Waiting...                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Current Task: Classifying adr-015.md                           │
│                                                                     │
│  📊 Processing Statistics:                                     │
│  - ADRs processed: 15/25                                     │
│  - Average time per ADR: 5.2 seconds                           │
│  - Estimated time remaining: 52 seconds                          │
│                                                                     │
│  You can safely close this page. Results will be saved.           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.4 Screen 4: Results Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ Analysis Complete! View Results →                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📊 Overview                                              │   │
│  │                                                         │   │
│  │  📁 Project: my-project-adrs                            │   │
│  │  📊 Total ADRs: 25                                     │   │
│  │  ⏱ Analyzed at: 2026-04-17 12:34:56                 │   │
│  │  ⚡️ Duration: 3m 42s                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🎯 Classification Results (Kruchten)                      │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────┐    │   │
│  │  │ Existence (ontocrisis)    ████████████ 60%  │    │   │
│  │  │ Property (diacrisis)      ██████░░░░░ 24%  │    │   │
│  │  │ Executive (pericrisis)     ████░░░░░░░ 12%  │    │   │
│  │  │ Ban (anticrisis)          ██░░░░░░░░░░ 4%   │    │   │
│  │  └───────────────────────────────────────────────┘    │   │
│  │                                                         │   │
│  │  Average confidence: 0.89                                │   │
│  │  High confidence (>0.8): 22/25 ADRs                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🔥 Topic Distribution                                     │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────┐    │   │
│  │  │ Database Migration         ████████░░░ 20%  │    │   │
│  │  │ API Design               ███████░░░░ 16%   │    │   │
│  │  │ Authentication            ██████░░░░░ 12%   │    │   │
│  │  │ Frontend Framework        ████░░░░░░░ 8%    │    │   │
│  │  │ ... (8 total topics)       ░░░░░░░░░░░ 44%   │    │   │
│  │  └───────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ✅ Quality & Compliance                                    │   │
│  │                                                         │   │
│  │  Template Adherence: 0.72/1.0 ⚠️ Needs improvement      │   │
│  │                                                         │   │
│  │  Top Issues:                                             │   │
│  │  🔴 40% missing "Alternatives" section                │   │
│  │  🟡 30% incomplete "Consequences" section                │   │
│  │  🟡 20% weak "Context" descriptions                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 💡 Key Insights (3 high priority)                       │   │
│  │                                                         │   │
│  │  🔴 [Quality] 40% of ADRs missing alternatives section  │   │
│  │       Click to view affected ADRs →                    │   │
│  │                                                         │   │
│  │  🟡 [Pattern] Recent ADRs show better context (5.2 avg) │   │
│  │       vs previous (3.8 avg) words                      │   │
│  │                                                         │   │
│  │  🟢 [Recommend] Consider Zimmermann for organizational   │   │
│  │       decisions (4 ADRs classified as Executive)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [View Dashboard] [View All ADRs] [Download Report]              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.5 Screen 5: ADR Detail View

```
┌─────────────────────────────────────────────────────────────────────┐
│  📄 ADR-001: Database Migration Strategy                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📊 Topic Analysis                                        │   │
│  │                                                         │   │
│  │  Primary Topic: Database Migration (0.85 probability)      │   │
│  │  Keywords: [database, migration, schema, postgresql]      │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────┐    │   │
│  │  │ Database Migration      ████████████ 85%  │    │   │
│  │  │ API Design              ███░░░░░░░░░ 15%  │    │   │
│  │  └───────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🎯 Classification (Kruchten)                              │   │
│  │                                                         │   │
│  │  Primary: Existence (ontocrisis)                         │   │
│  │  Confidence: 0.92 🔴 High                                 │   │
│  │                                                         │   │
│  │  Alternatives:                                            │   │
│  │  • Property (diacrisis) - 0.05                         │   │
│  │  • Executive (pericrisis) - 0.03                        │   │
│  │                                                         │   │
│  │  Explanation: This ADR describes a structural...        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ✅ Template Compliance                                    │   │
│  │                                                         │   │
│  │  Overall Score: 0.85/1.0 ✅ Good                       │   │
│  │                                                         │   │
│  │  Sections:                                               │   │
│  │  ✅ Context (presence: Yes, quality: Good)               │   │
│  │  ✅ Decision (presence: Yes, quality: Good)              │   │
│  │  ✅ Consequences (presence: Yes, quality: Good)           │   │
│  │  🔴 Alternatives (presence: No) - MISSING                  │   │
│  │  ✅ Status (presence: Yes, quality: Good)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 💡 Recommendations                                        │   │
│  │                                                         │   │
│  │  🔴 Add "Alternatives" section for completeness           │   │
│  │  🟡 Consider documenting migration rollback strategy      │   │
│  │  🟢 Similar ADRs: adr-003, adr-007, adr-012            │   │
│  │         (0.82, 0.78, 0.75 similarity)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [View ADR Content] [Compare with Similar] [Download Metadata]  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.6 Screen 6: Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Dashboard - my-project-adrs                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐   │
│  │ 📊25 │ 0.72│  8  │ 15  │ 0.89│ 45s │ 3.4m│ 25  │ 12h │   │
│  │ ADRs │Score│Topics│Exist│Conf│Last │Time │High │Ago │   │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📈 Topic Distribution Over Time                          │   │
│  │                                                         │   │
│  │  [Interactive line chart showing topic trends]            │   │
│  │                                                         │   │
│  │  Database Migration trend: ↗️ Increasing                 │   │
│  │  API Design trend: ↔️ Stable                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────┬───────────────────────────┐   │
│  │ 🎯 Classification Balance      │ ✅ Quality Trend          │   │
│  │                             │                            │   │
│  │  [Bar chart]                │ [Line chart]              │   │
│  │                             │                            │   │
│  │  Well-distributed            │ Improving over time        │   │
│  │  across categories            │ (0.65 → 0.72)            │   │
│  └──────────────────────────────┴───────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 💡 Insights by Priority                                  │   │
│  │                                                         │   │
│  │  🔴 High Priority (3)                                   │   │
│  │     • 40% missing alternatives section                    │   │
│  │     • Low confidence on adr-007 (0.68)                  │   │
│  │     • Inconsistent Status section usage                 │   │
│  │     [View All →]                                        │   │
│  │                                                         │   │
│  │  🟡 Medium Priority (5)                                  │   │
│  │     • Recent ADRs show better context descriptions          │   │
│  │     • Consider Zimmermann for organizational decisions    │   │
│  │     • 3 ADRs need review (low quality)                  │   │
│  │     [View All →]                                        │   │
│  │                                                         │   │
│  │  🟢 Low Priority (2)                                     │   │
│  │     • Topic diversity could be improved                   │   │
│  │     • No ADRs tagged as "Ban/Non-Existence"             │   │
│  │     [View All →]                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Export Dashboard] [Re-run Analysis] [Settings]               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Interactive Components

### 4.1 Interactive Charts

#### Topic Distribution (Pie Chart)
- Click slice → Filter ADRs by that topic
- Hover → Show exact percentage and count
- Toggle between views: Pie → Bar → Donut

#### Classification Balance (Bar Chart)
- Click bar → Show ADRs in that category
- Hover → Show count and percentage
- Sort by: Name → Count → Alphabetical

#### Quality Trend (Line Chart)
- Hover point → Show specific ADRs in that time period
- Zoom in/out for different time ranges
- Toggle: All ADRs → High quality → Low quality

#### Similarity Matrix (Heatmap)
- Click cell → Show detailed comparison
- Color scale: Green (similar) → Red (dissimilar)
- Show/hide labels for cleaner view

---

## 5. Filtering and Search

### 5.1 ADR List with Filters

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Search ADRs...                                          │
│                                                             │
│ Filters:                                                     │
│ Topic: [Database Migration ▼] (All topics)               │
│ Classification: [Existence ▼] (All categories)              │
│ Quality: [High ▼] (All levels)                          │
│ Date: [Last 30 days ▼]                                   │
│                                                             │
│ Found: 6 ADRs matching filters                             │
│                                                             │
│ ┌───────────────────────────────────────────────┐  │
│ │ 📄 ADR-001 | 🔥 Database Migration | 🎯 Existence │  │
│ │           ✅ 0.85 quality                     │  │
│ │           View Details →                       │  │
│ ├───────────────────────────────────────────────┤  │
│ │ 📄 ADR-003 | 🔥 Database Migration | 🎯 Existence │  │
│ │           ⚠️ 0.68 quality (needs review)       │  │
│ │           View Details →                       │  │
│ └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Export Options

### 6.1 Export Modal

```
┌─────────────────────────────────────────────────────────────────┐
│ 📤 Export Results                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                             │
│ Select format:                                               │
│ ◉ JSON (sidecar files)                                       │
│ ◉ Markdown report                                           │
│ ◉ PDF report                                                │
│ ◉ CSV (for spreadsheets)                                     │
│                                                             │
│ Include:                                                    │
│ ☑ Classification results                                    │
│ ☑ Topic analysis                                            │
│ ☑ Quality checks                                            │
│ ☑ Insights and recommendations                               │
│                                                             │
│ Filename: [my-project-adrs-analysis]                       │
│                                                             │
│              [Cancel]  [Export →]                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Responsive Design

### 7.1 Mobile (< 768px)
- Collapsible sidebar (hamburger menu)
- Stacked cards instead of side-by-side
- Simplified charts
- Touch-friendly buttons

### 7.2 Tablet (768px - 1024px)
- Sidebar becomes icon rail
- 2-column layout for charts
- Optimized table views

### 7.3 Desktop (> 1024px)
- Full sidebar navigation
- 3-4 column layouts
- Rich interactive charts
- Detailed ADR comparisons

---

## 8. Theme and Customization

### 8.1 Theme Options
- ☀️ Light Mode (default)
- 🌙 Dark Mode
- 🎨 Custom Theme (user selects colors)

### 8.2 User Preferences
- Default framework
- Preferred model
- Show/hide low-quality ADRs
- Insight priority threshold
- Chart preferences (colors, animations)

---

## 9. Performance Optimizations

### 9.1 Lazy Loading
- Only load ADR details when clicked
- Paginate ADR lists (25 per page)
- Defer non-critical charts

### 9.2 Caching
- Cache analysis results locally
- Store model embeddings in memory
- Persist dashboard state

### 9.3 Progressive Enhancement
- Show basic results first
- Load insights progressively
- Defer expensive visualizations

---

## 10. Key UI/UX Features

### 10.1 Status Indicators
- ✅ Complete (green)
- ⏳ In Progress (blue)
- ⏸ Waiting (gray)
- 🔴 Error (red)
- ⚠️ Warning (yellow)
- 🟢 Info (blue)

### 10.2 Interactive Elements
- Clickable charts with filters
- Expandable insight cards
- Real-time progress updates
- Drag-and-drop file upload
- Keyboard navigation support

### 10.3 Accessibility
- Screen reader compatible
- High contrast mode
- Keyboard shortcuts
- Focus indicators
- ARIA labels

---

## 11. CLI/TUI Interface Design

The CLI/TUI interface provides full feature parity with the Streamlit web UI, using modern terminal libraries for an intuitive experience.

  ### 11.1 Design Philosophy

  - **Consistent CLI**: Modern typer-based CLI with rich type hints and auto-help
  - **Rich Output**: Colored tables, progress bars, and formatted output using rich library
  - **Modern TUI**: Rich, interactive terminal UI using Textual (future enhancement)
  - **Natural Language**: Same agent-driven interface as Streamlit (future)
  - **Keyboard-First**: Optimized for keyboard navigation
  - **Progressive**: Simple commands for quick tasks, TUI for complex workflows
  - **Configuration-Driven**: .env + YAML config with `adrminer init` command
  ------- SEARCH
  ### 11.2 TUI Home Screen
  ### 11.2 CLI Entry Point

The CLI uses typer for modern, type-safe command-line interface with automatic help generation.

**Main Command Structure:**
```bash
adrminer [OPTIONS] COMMAND [ARGS]...

# Available commands:
  init         Initialize ADRminer configuration
  topics        Topic mining with BERTopic
  classify      Classify ADRs using LLM
  check         Check ADR quality and template adherence
  analyze       Run combined analysis
  model         Model management
  export        Export results and reports
  --help        Show help message
```

**Global Options:**
- `--config, -c`: Path to configuration file (default: ~/.adrminer.yaml)
- `--verbose, -v`: Verbose output
- `--version`: Show version information

**Exit Codes:**
- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Input file not found
- `4`: Model load error
- `5`: API error

### 11.3 Initialization Command

The `adrminer init` command sets up configuration for first-time users.

```bash
# Basic initialization (non-interactive)
adrminer init

# Interactive mode with prompts
adrminer init --interactive

# Specify custom config location
adrminer init --config /path/to/config.yaml

# Verbose mode
adrminer init --verbose
```

**What it does:**
1. Checks for `.env` file, creates from `.env.example` if missing
2. Creates `.adrminer.yaml` from packaged default config
3. Validates configuration structure
4. Checks for default topic model availability
5. Sets up required directory structure
6. Validates LLM API keys if provided

**Example Output:**
```
✅ ADRminer Configuration Initialization

Checking environment...
  ✓ .env file found at /home/user/.adrminer/.env
  ✓ OPENAI_API_KEY configured

Creating configuration...
  ✓ Configuration file created at /home/user/.adrminer.yaml
  ✓ Default topic model: ~/.adrminer/models/topic_model

Validating configuration...
  ✓ YAML structure valid
  ✓ Topic model accessible
  ✓ Examples loaded

Configuration initialized successfully! Run 'adrminer --help' to get started.
```

### 11.4 Configuration Management

**Configuration Files:**

1. **`.env`** (environment variables - sensitive data only):
```bash
# LLM Provider Keys
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

2. **`.adrminer.yaml`** (user configuration):
```yaml
# LLM Configuration
llm:
  provider: openai  # openai, anthropic, ollama, azure, google
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 2000

# Topic Model Configuration
topic_model:
  path: ~/.adrminer/models/topic_model
  embedding_model: all-MiniLM-L6-v2
  n_topics: auto

# Classification Configuration
classification:
  framework: kruchten  # kruchten, quality_attributes, zimmermann
  examples: ~/.adrminer/examples/kruchten_examples.json
  use_examples: true

# Check Service Configuration
check:
  template: madr
  model: gpt-4o-mini

# Output Configuration
output:
  format: json-sidecar  # json-sidecar, consolidated-json, markdown
  parallel: true
  verbose: false
```

**Environment Variable Overrides:**
```bash
# Override LLM provider from config
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-sonnet

# Override topic model path
export TOPIC_MODEL_PATH=/custom/path/to/model

# Use different examples
export CLASSIFICATION_EXAMPLES=/custom/examples.json
```

### 11.5 Topics Command

```bash
# Predict topics for single ADR
adrminer topics predict adr-001.md

# Predict topics for directory
adrminer topics predict ./adrs/ --parallel

# Train new topic model
adrminer topics train ./training_data/ --output ./models/custom --n-topics 15

# Model management
adrminer topics list
adrminer topics info topic-model-v1.0
```

**Topics Subcommands:**
- `predict`: Predict topics for ADR(s)
- `train`: Train new topic model
- `list`: List available topic models
- `info`: Show model details

**Predict Options:**
- `--model, -m`: Path to topic model (default from config)
- `--output, -o`: Output JSON file path
- `--parallel, -p`: Enable parallel processing for batches
- `--threshold, -t`: Topic probability threshold (default: 0.0)
- `--multiple`: Allow multiple topics per ADR
- `--verbose, -v`: Verbose output

**Train Options:**
- `--n-topics, -n`: Number of topics (default: auto)
- `--embedding, -e`: Embedding model (default: all-MiniLM-L6-v2)
- `--openai`: Use OpenAI for topic labels
- `--output, -o`: Output model directory

### 11.6 Classify Command

```bash
# Classify single ADR
adrminer classify predict adr-001.md --framework kruchten

# Classify directory with default framework from config
adrminer classify predict ./adrs/ --parallel

# Zero-shot (no examples)
adrminer classify predict adr-001.md --framework qas --no-examples

# Custom examples
adrminer classify predict ./adrs/ --examples /path/to/custom.json

# Framework options
adrminer classify --framework kruchten      # 4 categories
adrminer classify --framework quality_attributes  # 10 categories
adrminer classify --framework zimmermann     # 9 categories
```

**Classify Subcommands:**
- `predict`: Classify ADR(s) using specified framework
- `list`: List supported frameworks
- `examples`: Show available example sets

**Predict Options:**
- `--framework, -f`: Classification framework (kruchten, quality_attributes, zimmermann)
- `--examples, -e`: Path to custom examples JSON file
- `--no-examples`: Zero-shot classification (no examples)
- `--parallel, -p`: Enable parallel processing for batches
- `--output, -o`: Output JSON file path
- `--verbose, -v`: Verbose output

### 11.7 Check Command

```bash
# Check single ADR
adrminer check predict adr-001.md

# Check directory
adrminer check predict ./adrs/ --parallel

# Section-wise analysis
adrminer check predict adr-001.md --sections

# Template options
adrminer check predict adr-001.md --template madr
```

**Check Subcommands:**
- `predict`: Check ADR quality and template adherence
- `templates`: List supported templates

**Predict Options:**
- `--template, -t`: Template to check against (default: madr)
- `--sections`: Run section-wise analysis
- `--parallel, -p`: Enable parallel processing for batches
- `--output, -o`: Output JSON file path
- `--verbose, -v`: Verbose output

### 11.8 Analyze Command (Combined)

```bash
# Run all services
adrminer analyze ./adrs/ --topics --classify kruchten --check

# Use default configuration
adrminer analyze ./adrs/

# Export results
adrminer analyze ./adrs/ --output ./results/

# Generate insights
adrminer analyze ./adrs/ --insights

# Consolidated JSON output
adrminer analyze ./adrs/ --format consolidated-json --output ./results/summary.json
```

**Analyze Options:**
- `--topics`: Enable topic mining
- `--classify, -f`: Enable classification with framework
- `--check`: Enable quality checking
- `--insights`: Generate cross-service insights
- `--format, -f`: Output format (json-sidecar, consolidated-json, markdown)
- `--output, -o`: Output directory or file
- `--parallel, -p`: Enable parallel processing
- `--verbose, -v`: Verbose output

### 11.9 Export Command

```bash
# Export to JSON sidecars
adrminer export --format json-sidecar --input ./results/ --output ./adrs/

# Consolidated JSON export
adrminer export --format consolidated-json --input ./results/ --output ./summary.json

# Markdown report
adrminer export --format markdown --input ./results/ --output ./report.md

# Export specific analysis
adrminer export --type topics --format json-sidecar --input ./results/
```

**Export Options:**
- `--format, -f`: Output format (json-sidecar, consolidated-json, markdown)
- `--type, -t`: Analysis type to export (topics, classification, check, all)
- `--input, -i`: Input results directory
- `--output, -o`: Output directory or file
- `--include-insights`: Include generated insights

### 11.10 Model Command

```bash
# List available models
adrminer model list

# Show model details
adrminer model info topic-model-v1.0

# Validate model
adrminer model validate --model ./models/custom
```

**Model Subcommands:**
- `list`: List all available models
- `info`: Show detailed model information
- `validate`: Validate model file integrity
- `download`: Download model from repository (future)

### 11.11 Rich Output Examples

**Table Display:**
```python
from rich.table import Table
from rich.console import Console

console = Console()

table = Table(title="Classification Results")
table.add_column("ADR", style="cyan")
table.add_column("Category", style="green")
table.add_column("Confidence", style="yellow")
table.add_column("Status", style="bold")

table.add_row("adr-001.md", "Existence", "0.92", "✅")
table.add_row("adr-002.md", "Property", "0.78", "⚠️")

console.print(table)
```

**Progress Bar:**
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0}%"),
    console=console
) as progress:
    task = progress.add_task("Processing ADRs...", total=100)
    for i in range(100):
        # Process ADR
        progress.update(task, advance=1)
```

**Progress with Multiple Services:**
```python
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    console=console
) as progress:
    topics_task = progress.add_task("Topics: ", total=25)
    classify_task = progress.add_task("Classification: ", total=25)
    check_task = progress.add_task("Checking: ", total=25)
    
    # Process with parallel execution
    for i in range(25):
        progress.update(topics_task, advance=1)
        progress.update(classify_task, advance=1)
        progress.update(check_task, advance=1)
```

### 11.12 Error Handling

**Clear Error Messages:**
```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def handle_error(error: Exception, context: str = None):
    """Handle and display errors with rich formatting"""
    error_msg = f"""
# ❌ Error

{error}

**Context:** {context if context else "Unknown"}

**Suggestions:**
- Run `adrminer init` to set up configuration
- Check API keys in `.env` file
- Verify model files exist at configured paths
- Use `--verbose` flag for more details
- Check documentation: `adrminer --help`

For more help, visit: https://github.com/tommantonela/ADRminer
    """
    console.print(Markdown(error_msg))
```

**Exit Codes:**
```python
import typer
import sys

# Configuration error
raise typer.Exit(
    message="Configuration file not found. Run 'adrminer init' first.",
    code=2
)

# File not found
raise typer.Exit(
    message=f"File not found: {input_path}",
    code=3
)

# Model load error
raise typer.Exit(
    message=f"Failed to load model: {model_path}",
    code=4
)

# API error
raise typer.Exit(
    message=f"LLM API error: {error_message}",
    code=5
)
```

### 11.13 TUI Home Screen (Future Enhancement)


### 11.2 TUI Home Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🏗️ ADRminer - Analyze Your Architectural Decisions                    │
│                                                                      │
│  Welcome! ADRminer helps you analyze, improve, and understand your       │
│  Architectural Decision Records (ADRs).                                 │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  📊 Topics  │  │  🎯 Classify │  │  ✅ Check    │                │
│  │  Discover   │  │  Categorize  │  │  Quality     │                │
│  │  what       │  │  decisions   │  │  and         │                │
│  │  matters    │  │  by type     │  │  compliance  │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📁 Quick Start: Analyze Your First ADRs                      │   │
│  │                                                              │   │
│  │  [1] Upload folder of ADRs                                   │   │
│  │  [2] Paste ADR text                                          │   │
│  │  [3] Use natural language: "Analyze all ADRs in ./adrs"        │   │
│  │                                                              │   │
│  │  Select services: [ ] Topics [ ] Classification [ ] Checking   │   │
│  │  Generate insights: [✓]                                       │   │
│  │                                                              │   │
│  │  [Analyze →]  [Help]  [Quit]                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📚 Recent Analyses                                            │   │
│  │                                                              │   │
│  │  • my-project (25 ADRs) - 2 hours ago                       │   │
│  │  • frontend-team (12 ADRs) - 1 day ago                       │   │
│  │  • backend-service (18 ADRs) - 3 days ago                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [N] Natural Language  [C] Command Line  [T] Terminal UI  [Q] Quit  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 TUI Analyze Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 Analyze ADRs                                                │
│                                                                      │
│  Step 1: Select Input                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  ○ Single ADR (text)                                             │   │
│    [Paste text here...]                                            │   │
│    or [Upload ADR file...]                                       │   │
│                                                              │   │
│  ● Folder of ADRs (selected)                                      │   │
│    Path: /path/to/adrs                                          │   │
│    Found: 25 ADR files                                           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Step 2: Choose Services                                         │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  [✓] Topic Mining                                             │   │
│    Model: Pre-trained v1.0 [▼]                                  │   │
│    Topics: Auto [▼]                                             │   │
│                                                              │   │
│  [✓] Classification                                            │   │
│    Framework: Kruchten [▼] (Quality Attributes, Zimmermann)        │   │
│    Examples: Built-in [▼] (None, Custom, Built-in)             │   │
│                                                              │   │
│  [✓] ADR Checking                                             │   │
│    Template: MADR [▼]                                          │   │
│                                                              │   │
│  [✓] Generate Insights                                        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Step 3: Output Options                                           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  [✓] JSON sidecar files                                       │   │
│  [✓] Markdown report                                          │   │
│  [✓] Create dashboard                                          │   │
│    Output: Same as input [▼]                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│                                  [Start Analysis →]   [Back] [Quit]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.4 TUI Progress Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⏳ Processing ADRs...                                            │
│                                                                      │
│  Overall Progress: ████████████░░░░░░░░░░ 60%                      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ ✅ Topic Mining (25/25) - 45 seconds                        │   │
│  │                                                              │   │
│  │ ⏳ Classification (15/25) - 2:15 elapsed                     │   │
│  │    ███████████████░░░░░░░░░░░░░░ 60%                     │   │
│  │                                                              │   │
│  │ ⏸ ADR Checking (0/25) - Waiting...                           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Current: Classifying adr-015.md                                     │
│                                                                      │
│  📊 Statistics:                                                    │
│  • ADRs processed: 15/25                                         │
│  • Average time: 5.2 seconds/ADR                                   │
│  • Estimated remaining: 52 seconds                                   │
│                                                                      │
│  [P] Pause  [C] Cancel  [Q] Quit (results will be saved)             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.5 TUI Results Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ✅ Analysis Complete!                                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📊 Overview                                                  │   │
│  │                                                              │   │
│  │  📁 Project: my-project-adrs                                 │   │
│  │  📊 Total ADRs: 25                                          │   │
│  │  ⏱ Analyzed at: 2026-04-17 12:34:56                        │   │
│  │  ⚡ Duration: 3m 42s                                        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 🎯 Classification (Kruchten)                                 │   │
│  │                                                              │   │
│  │  Existence (ontocrisis)    ████████████ 60% (15 ADRs)       │   │
│  │  Property (diacrisis)      ██████░░░░░ 24% (6 ADRs)         │   │
│  │  Executive (pericrisis)     ████░░░░░░ 12% (3 ADRs)        │   │
│  │  Ban (anticrisis)          ██░░░░░░░░ 4% (1 ADR)          │   │
│  │                                                              │   │
│  │  Average confidence: 0.89                                       │   │
│  │  High confidence (>0.8): 22/25 ADRs                            │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 🔥 Topic Distribution                                        │   │
│  │                                                              │   │
│  │  Database Migration         ████████░░░ 20% (5 ADRs)          │   │
│  │  API Design               ███████░░░░ 16% (4 ADRs)          │   │
│  │  Authentication            ██████░░░░░ 12% (3 ADRs)          │   │
│  │  Frontend Framework        ████░░░░░░░ 8% (2 ADRs)          │   │
│  │  Other topics             ████████░░░ 44% (11 ADRs)         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ ✅ Quality & Compliance                                      │   │
│  │                                                              │   │
│  │  Template Adherence: 0.72/1.0 ⚠️ Needs improvement           │   │
│  │                                                              │   │
│  │  Top Issues:                                                  │   │
│  │  🔴 40% missing "Alternatives" section                       │   │
│  │  🟡 30% incomplete "Consequences" section                     │   │
│  │  🟡 20% weak "Context" descriptions                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [D] Dashboard  [A] All ADRs  [E] Export  [Q] Quit                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.6 TUI ADR Detail View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📄 ADR-001: Database Migration Strategy                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📊 Topic Analysis                                             │   │
│  │                                                              │   │
│  │  Primary: Database Migration (0.85 prob)                        │   │
│  │  Keywords: [database, migration, schema, postgresql]             │   │
│  │                                                              │   │
│  │  Database Migration      ████████████ 85%                        │   │
│  │  API Design              ███░░░░░░░░ 15%                        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 🎯 Classification (Kruchten)                                  │   │
│  │                                                              │   │
│  │  Primary: Existence (ontocrisis)                               │   │
│  │  Confidence: 0.92 🔴 High                                    │   │
│  │                                                              │   │
│  │  Alternatives:                                                 │   │
│  │  • Property (diacrisis) - 0.05                               │   │
│  │  • Executive (pericrisis) - 0.03                             │   │
│  │                                                              │   │
│  │  Explanation: This ADR describes a structural change to...        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ ✅ Template Compliance                                        │   │
│  │                                                              │   │
│  │  Overall Score: 0.85/1.0 ✅ Good                             │   │
│  │                                                              │   │
│  │  ✅ Context (presence: Yes, quality: Good)                       │   │
│  │  ✅ Decision (presence: Yes, quality: Good)                      │   │
│  │  ✅ Consequences (presence: Yes, quality: Good)                   │   │
│  │  🔴 Alternatives (presence: No) - MISSING                         │   │
│  │  ✅ Status (presence: Yes, quality: Good)                        │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 💡 Recommendations                                           │   │
│  │                                                              │   │
│  │  🔴 Add "Alternatives" section for completeness                  │   │
│  │  🟡 Consider documenting migration rollback strategy                 │   │
│  │  🟢 Similar ADRs: adr-003, adr-007, adr-012                 │   │
│  │         (0.82, 0.78, 0.75 similarity)                       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [V] View ADR  [C] Compare  [D] Download  [N] Next  [Q] Quit       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.7 TUI Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 Dashboard - my-project-adrs                                   │
│                                                                      │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐           │
│  │ 📊25│ 0.72│  8  │ 15  │ 0.89│ 45s │ 3.4m│ 25  │ 12h │           │
│  │ ADRs │Score│Topics│Exist│Conf│Last │Time │High │Ago │           │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 📈 Topic Distribution Over Time                            │   │
│  │                                                              │   │
│  │  Jan  Feb  Mar  Apr  May  Jun                                │   │
│  │  Database:     2    5    8   12   15   15 (↗️)                │   │
│  │  API Design:   1    2    3    4    4    4 (→)                 │   │
│  │  Auth:        0    1    2    3    3    3 (→)                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────┬───────────────────────────┐           │
│  │ 🎯 Classification Balance    │ ✅ Quality Trend         │           │
│  │                             │                          │           │
│  │  Existence     15 ████████ │ 0.65 ──► 0.72         │           │
│  │  Property       6  █████    │                          │           │
│  │  Executive     3  ███      │ Improving ↑             │           │
│  │  Ban           1  ██       │                          │           │
│  └──────────────────────────────┴───────────────────────────┘           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ 💡 Insights by Priority                                     │   │
│  │                                                              │   │
│  │  🔴 High Priority (3)                                       │   │
│  │     • 40% missing alternatives section                         │   │
│  │     • Low confidence on adr-007 (0.68)                       │   │
│  │     • Inconsistent Status section usage                        │   │
│  │     [View All]                                              │   │
│  │                                                              │   │
│  │  🟡 Medium Priority (5)                                     │   │
│  │     • Recent ADRs show better context descriptions               │   │
│  │     • Consider Zimmermann for organizational decisions           │   │
│  │     • 3 ADRs need review (low quality)                       │   │
│  │     [View All]                                              │   │
│  │                                                              │   │
│  │  🟢 Low Priority (2)                                        │   │
│  │     • Topic diversity could be improved                        │   │
│  │     • No ADRs tagged as "Ban/Non-Existence"                  │   │
│  │     [View All]                                              │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [E] Export  [R] Re-run  [S] Settings  [Q] Quit                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.8 CLI Command Examples

#### Traditional CLI Commands

```bash
# Analyze with specific services
adrminer analyze ./adrs --topics --classify --framework kruchten --check

# Single ADR analysis
adrminer analyze adr-001.md --topics --classify --framework qas

# Natural language interface
adrminer "Classify all ADRs using Zimmermann framework"

# View results
adrminer results --latest
adrminer results adr-001.md

# Export reports
adrminer export --format json --output ./reports
adrminer export --format markdown --output ./reports/summary.md

# Model management
adrminer model list
adrminer model info topic-model-v1.0
adrminer train topics ./custom-adrs --output ./models/custom
```

#### Natural Language CLI

```bash
# Natural language queries
adrminer "Analyze all ADRs in ./docs/adrs with topic mining and classification"
adrminer "Which ADRs are missing the alternatives section?"
adrminer "Show me the topic distribution for my ADRs"
adrminer "Check the quality of adr-015.md"

# Follow-up questions (context-aware)
adrminer "What's the average confidence for classification?"
adrminer "Which ADRs are similar to adr-001.md?"
adrminer "Generate a report of all low-quality ADRs"
```

### 11.9 Implementation Libraries

```python
# TUI Implementation (Textual)
from textual.app import App
from textual.widgets import Header, Footer, Static, ProgressBar
from textual.containers import Horizontal, Vertical
from rich.table import Table
from rich.console import Console

class ADRminerTUI(App):
    """Modern terminal UI for ADRminer."""
    
    def __init__(self):
        super().__init__()
        self.console = Console()
    
    def compose(self):
        yield Header()
        yield HomeScreen()
        yield Footer()
    
    def on_home_analyze(self):
        """Navigate to analyze screen."""
        self.push_screen(AnalyzeScreen())
    
    def on_home_natural_language(self, query):
        """Process natural language query."""
        result = self.agent.process(query, context=self.context)
        self.push_screen(ResultsScreen(result))

# CLI Implementation (Click)
import click
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.console import Console

console = Console()

@click.group()
def cli():
    """ADRminer - Analyze your architectural decisions."""
    pass

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--topics', is_flag=True, help='Run topic mining')
@click.option('--classify', is_flag=True, help='Run classification')
@click.option('--framework', type=click.Choice(['kruchten', 'qas', 'zimmermann']))
@click.option('--check', is_flag=True, help='Run quality checks')
def analyze(path, topics, classify, framework, check):
    """Analyze ADRs from a file or directory."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing ADRs...", total=100)
        
        # Run analysis using unified agent
        agent = ADRminerAgent()
        result = agent.process(
            f"Analyze {path} with topics={topics}, "
            f"classification={classify} using {framework}, "
            f"checks={check}",
            context={"adr_path": path}
        )
        
        progress.update(task, completed=100)
    
    # Display results in rich table
    table = Table(title="Analysis Results")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total ADRs", str(result['adr_count']))
    table.add_row("Quality Score", str(result['quality_score']))
    console.print(table)

# Natural language CLI
@cli.command()
@click.argument('query')
def chat(query):
    """Chat with ADRminer using natural language."""
    agent = ADRminerAgent()
    result = agent.process(query, context={})
    console.print(result['response'])
```

### 11.10 CLI/TUI Benefits

1. **Full Feature Parity**: All Streamlit features available in terminal
2. **Performance**: No browser overhead, direct terminal output
3. **Scriptable**: Easy to integrate into CI/CD pipelines
4. **Natural Language**: Same agent interface as web UI
5. **Keyboard-First**: Fast navigation for power users
6. **Offline Capable**: Can work entirely offline with local models
7. **Debugging**: Easier to debug with direct terminal output
8. **Remote Access**: Works over SSH without browser

---

**Document History:**
- v1.0 - Initial UI/UX design document (2026-04-17)
- v1.1 - Added CLI/TUI interface design (2026-04-18)
