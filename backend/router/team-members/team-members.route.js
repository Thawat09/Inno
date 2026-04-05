const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /team-members" }));
router.post('/', (req, res) => res.json({ message: "POST /team-members" }));
router.put('/:id', (req, res) => res.json({ message: "PUT /team-members/:id" }));

module.exports = router;