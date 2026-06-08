# Essential Workflow Regression Checklist

Run affected checks after every repair. Run the complete list before production
promotion. A task cannot be marked complete while an affected workflow fails.

## Public Desktop and Mobile

- [ ] Home renders without a blank or stuck launch state.
- [ ] Initial course rows render correct thumbnails and can scroll.
- [ ] Mobile navigation opens as a floating panel without moving page content.
- [ ] Courses page filters, sorting, pagination, and list/grid modes work.
- [ ] Search returns results and opens a course.
- [ ] Subjects page shows only non-empty subjects with accurate counts.
- [ ] Subject detail results match the selected subject and remain correctly ordered.
- [ ] Universities page and university detail listings work.
- [ ] Course detail opens, back navigation works, and the selected lecture plays.
- [ ] Source, lecture-note, and exam links remain available where present.
- [ ] Roadmaps preserve entry order and course links.
- [ ] Error, empty, loading, and retry states remain usable.

## Accounts and User Data

- [ ] Registration and login work.
- [ ] Existing user login remains valid after auth changes.
- [ ] Saving and removing a library course works.
- [ ] Existing library relationships remain unchanged after unrelated repairs.
- [ ] Watch history records and continue-watching links resume the intended lecture.
- [ ] Existing watch-history relationships remain unchanged after unrelated repairs.

## Admin

- [ ] Admin login and protected navigation work.
- [ ] Statistics load.
- [ ] Course audit and editing work.
- [ ] Publishing and unpublishing produce the intended public visibility.
- [ ] Pending-review, universities, sources, and scraper status load.

## PWA and Mobile Launch

- [ ] Fresh browser visit has no black/white dead period.
- [ ] Fresh home-screen install launches with the intended icon and splash.
- [ ] Existing installed PWA upgrades without becoming stuck or stale.
- [ ] Reopening after inactivity remains usable.
- [ ] Offline/reconnection behavior matches the currently approved capability.

## Deployment and Data

- [ ] Local branch, pushed commit, Netlify deploy, and Render deploy are identified.
- [ ] Public API health and representative routes return expected schemas.
- [ ] Catalog, video, subject, roadmap, user, library, and history counts do not
      unexpectedly decrease.
- [ ] Foreign-key relationships and uniqueness checks remain valid.
- [ ] No secret appears in tracked files, generated reports, or logs.
