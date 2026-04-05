const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /leave-requests" }));
router.post('/', (req, res) => res.json({ message: "POST /leave-requests" }));
router.put('/:id', (req, res) => res.json({ message: "PUT /leave-requests/:id" }));

module.exports = router;