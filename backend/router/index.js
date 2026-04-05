const router = require("express").Router();

// Auth
router.use('/auth', require('./auth/auth.route'));

// Users / Roles
router.use('/users', require('./users/users.route'));
router.use('/locked-users', require('./locked-users/locked-users.route'));

// Teams / Membership
router.use('/teams', require('./teams/teams.route'));
router.use('/sub-teams', require('./sub-teams/sub-teams.route'));
router.use('/team-members', require('./team-members/team-members.route'));

// Standby / Calendar
router.use('/standby', require('./standby/standby.route'));

// Leave / Availability
router.use('/leave-requests', require('./leave-requests/leave-requests.route'));
router.use('/availability', require('./availability/availability.route'));

// Tickets
router.use('/tickets', require('./tickets/tickets.route'));

// Routing / Notification / Acceptance Monitor / Escalation Rules
router.use('/routing', require('./routing/routing.route'));
router.use('/notifications', require('./notifications/notifications.route'));
router.use('/acceptance-monitor', require('./acceptance-monitor/acceptance-monitor.route'));
router.use('/escalation-rules', require('./escalation-rules/escalation-rules.route'));

// LINE
router.use('/line', require('./line/line.route'));

// Reports
router.use('/reports', require('./reports/reports.route'));

// Audit & AI
router.use('/audit-logs', require('./audit-logs/audit-logs.route'));
router.use('/ai', require('./ai/ai.route'));

// Mapping & Search
router.use('/data-mapping', require('./data-mapping/data-mapping.route'));
router.use('/search', require('./search/search.route'));

module.exports = router;