const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /teams" }));

module.exports = router;