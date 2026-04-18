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

**Document History:**
- v1.0 - Initial UI/UX design document (2026-04-17)