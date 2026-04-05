const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /users" }));
router.get('/:id', (req, res) => res.json({ message: `GET /users/${req.params.id}` }));
router.post('/', (req, res) => res.json({ message: "POST /users" }));
router.put('/:id', (req, res) => res.json({ message: "PUT /users/:id" }));
router.patch('/:id/status', (req, res) => res.json({ message: "PATCH /users/:id/status" }));
router.put('/:id/roles', (req, res) => res.json({ message: "PUT /users/:id/roles" }));

module.exports = router;