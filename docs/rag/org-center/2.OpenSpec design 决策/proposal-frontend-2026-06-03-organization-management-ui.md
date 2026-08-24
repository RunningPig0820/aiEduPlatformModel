## Why

The platform currently lacks organization-level management capabilities, preventing schools from managing their structure, faculty, and permissions in a unified way. Users (teachers, students, parents) are not associated with school organizations, making it impossible to implement role-based access control at the school level. This change introduces organization management to enable school-level governance and prepare for future permission management features.

## What Changes

- **New**: School organization management - create, view, and manage school entities
- **New**: School profile fields: name, icon/logo, school type, educational stages (学段)
- **New**: Faculty/staff management under school organization
- **New**: Organization-based user association and permission foundation

## Capabilities

### New Capabilities

- `school-organization`: School entity creation and management with profile fields (name, icon, type, educational stages). Provides the foundation for organization-level governance.
- `faculty-management`: Teacher and staff management within school organizations. Enables viewing, adding, and managing faculty members.

### Modified Capabilities

<!-- No existing capabilities are modified - this is a new domain -->

## Impact

- **New Pages**: Organization management dashboard, school creation/edit page, faculty management page
- **New API Endpoints**: School CRUD operations, faculty management operations
- **Data Model**: New entities for school organization, faculty-staff association
- **Navigation**: Add organization management entry in admin/teacher dashboard
- **Future**: Sets foundation for permission management (role management, department management)