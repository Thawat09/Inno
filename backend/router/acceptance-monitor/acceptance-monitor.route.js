const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /acceptance-monitor" }));

module.exports = router;