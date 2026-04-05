const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /audit-logs" }));

module.exports = router;