const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /data-mapping" }));
router.post('/', (req, res) => res.json({ message: "POST /data-mapping" }));
router.put('/:id', (req, res) => res.json({ message: "PUT /data-mapping/:id" }));
router.delete('/:id', (req, res) => res.json({ message: "DELETE /data-mapping/:id" }));

module.exports = router;