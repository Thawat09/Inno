const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /locked-users" }));
router.post('/:id/unlock', (req, res) => res.json({ message: "POST /locked-users/:id/unlock" }));

module.exports = router;