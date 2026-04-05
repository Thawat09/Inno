const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /availability" }));
router.post('/', (req, res) => res.json({ message: "POST /availability" }));
router.put('/:id', (req, res) => res.json({ message: "PUT /availability/:id" }));

module.exports = router;