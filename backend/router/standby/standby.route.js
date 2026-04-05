const router = require("express").Router();

router.get('/calendars', (req, res) => res.json({ message: "GET /standby/calendars" }));
router.post('/calendars', (req, res) => res.json({ message: "POST /standby/calendars" }));
router.put('/calendars/:id', (req, res) => res.json({ message: "PUT /standby/calendars/:id" }));

router.get('/slots', (req, res) => res.json({ message: "GET /standby/slots" }));
router.post('/slots', (req, res) => res.json({ message: "POST /standby/slots" }));
router.put('/slots/:id', (req, res) => res.json({ message: "PUT /standby/slots/:id" }));
router.post('/slots/:id/replace', (req, res) => res.json({ message: "POST replace standby slot" }));

router.get('/current', (req, res) => res.json({ message: "GET /standby/current" }));

module.exports = router;