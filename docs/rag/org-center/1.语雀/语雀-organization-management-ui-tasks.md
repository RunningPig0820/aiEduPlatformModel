# tasks（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/organization-management-ui-tasks
> 字数：163 ｜ 下载：2026-08-24

## 1. Setup

- [x] 1.1 Create organization pages directory structure (`pages/organization/`)
- [x] 1.2 Add organization API endpoints to `src/js/api.js`
- [x] 1.3 Create Alpine.js data models for school and faculty entities

## 2. School Organization UI

- [x] 2.1 Create school list page (`pages/organization/schools.html`)
- [x] 2.2 Implement school list Alpine.js component with pagination
- [x] 2.3 Create school creation/edit page (`pages/organization/school-edit.html`)
- [x] 2.4 Implement school form with fields: name, icon upload, type selection, stage multi-select
- [x] 2.5 Create school detail page (`pages/organization/school-detail.html`)
- [x] 2.6 Implement school detail view with faculty section navigation

## 3. Faculty Management UI

- [x] 3.1 Create faculty management section in school detail page
- [x] 3.2 Implement faculty list component with pagination
- [x] 3.3 Add faculty member info display (name, role/title)
- [x] 3.4 Implement empty state display for faculty list

## 4. Integration

- [x] 4.1 Add organization management entry in navigation
- [x] 4.2 Integrate school icon upload with existing image handling
- [x] 4.3 Ensure responsive design with Tailwind + daisyUI components
- [x] 4.4 Test school CRUD flow end-to-end
- [x] 4.5 Test faculty list browsing under school context
