const router = require("express").Router();

router.get('/global', (req, res) => res.json({ message: "GET /search/global" }));

module.exports = router;