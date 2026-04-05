const router = require("express").Router();

router.get('/', (req, res) => res.json({ message: "GET /escalation-rules" }));
router.get('/:id', (req, res) => res.json({ message: `GET /escalation-rules/${req.params.id}` }));
router.post('/', (req, res) => res.json({ message: `POST /escalation-rules` }));
router.put('/:id', (req, res) => res.json({ message: `PUT /escalation-rules/${req.params.id}` }));
router.patch('/:id/status', (req, res) => res.json({ message: `PATCH /escalation-rules/${req.params.id}/status` }));
router.delete('/:id', (req, res) => res.json({ message: `DELETE /escalation-rules/${req.params.id}` }));

module.exports = router;