const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /sub-teams" }));

module.exports = router;