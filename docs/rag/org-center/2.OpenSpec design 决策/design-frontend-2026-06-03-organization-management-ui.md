## Context

The AI Education Platform currently operates without organization-level structure. Users (students, teachers, parents) exist in isolation without school association. This limits the ability to:
- Implement school-level permission controls
- Manage faculty by school
- Organize students by school and class

The platform uses a multi-page architecture with Vite, Tailwind + daisyUI for styling, and Alpine.js for interactivity. Frontend should maintain the existing design patterns.

## Goals / Non-Goals

**Goals:**
- Create school organization entities with core profile fields
- Enable faculty management under school context
- Maintain existing frontend design patterns
- Set foundation for future permission management features

**Non-Goals:**
- Department and user management (future iteration)
- Position and role management (future iteration)
- Student management (行政班管理) (future iteration)
- Academic year/semester management
- Third-party sync (钉钉/乐课网)
- Permission system implementation

## Decisions

### 1. Page Structure

**Decision**: Create dedicated organization management pages under new `/pages/organization/` directory.

**Alternatives Considered**:
- Add to existing teacher dashboard → Rejected: cluttered UI, organization management is cross-role
- Single page with tabs → Rejected: faculty and school settings are different concerns

**Rationale**: Clean separation, extensible for future features (department, role management).

### 2. School Data Model

**Decision**: School entity with fields: name, icon/logo URL, type (enum), educational stages (multi-select array).

**Fields**:
- `name`: String, required - school display name
- `icon`: String (URL) - school logo image
- `type`: Enum (KINDERGARTEN, PRIMARY, JUNIOR, SENIOR, COMPREHENSIVE) - school category
- `stages`: Array of enums - educational stages covered (小学, 初中, 高中, etc.)

### 3. Faculty Association

**Decision**: Faculty members associated with school via `schoolId` field in user profile.

**Rationale**: Simple association, supports future expansion (department, position).

### 4. API Endpoints

**Decision**: RESTful endpoints under `/api/organization/`:
- `GET /api/organization/schools` - List schools
- `POST /api/organization/schools` - Create school
- `GET /api/organization/schools/:id` - Get school details
- `PUT /api/organization/schools/:id` - Update school
- `GET /api/organization/schools/:id/faculty` - List faculty under school

### 5. Frontend Components

**Decision**: Use Alpine.js components following existing patterns (similar to `studentApp()` structure).

**Rationale**: Consistent with existing pages, lightweight, maintainable.

## Risks / Trade-offs

**Risk**: School creation without permission guard → Mitigation: Initial version for admin use only; permission checks added in future iteration.

**Risk**: Faculty list may grow large → Mitigation: Pagination support in API from day one.

**Trade-off**: Simplified data model (no department/position yet) → Acceptable: MVP scope, can extend later without breaking changes.