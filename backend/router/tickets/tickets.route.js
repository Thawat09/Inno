const router = require("express").Router();

// GET Endpoints
router.get('/', (req, res) => res.json({ message: "GET /tickets" }));
router.get('/:id', (req, res) => res.json({ message: `GET /tickets/${req.params.id}` }));
router.get('/:id/classification', (req, res) => res.json({ message: "GET ticket classification" }));
router.get('/:id/notifications', (req, res) => res.json({ message: "GET ticket notifications" }));
router.get('/:id/acceptance', (req, res) => res.json({ message: "GET ticket acceptance" }));
router.get('/:id/escalations', (req, res) => res.json({ message: "GET ticket escalations" }));
router.get('/:id/artifacts', (req, res) => res.json({ message: "GET ticket artifacts" }));
router.get('/:id/contacts', (req, res) => res.json({ message: "GET ticket contacts" }));

// POST Endpoints (Actions)
router.post('/:id/accept', (req, res) => res.json({ message: "POST accept ticket" }));
router.post('/:id/override', (req, res) => res.json({ message: "POST manual override ticket" }));
router.post('/:id/reroute', (req, res) => res.json({ message: "POST reroute ticket" }));

module.exports = router;