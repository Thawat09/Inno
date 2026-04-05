const router = require("express").Router();

router.get('/sla/team', (req, res) => res.json({ message: "GET /reports/sla/team" }));
router.get('/sla/subteam', (req, res) => res.json({ message: "GET /reports/sla/subteam" }));
router.get('/export/csv', (req, res) => res.json({ message: "GET /reports/export/csv" }));

module.exports = router;