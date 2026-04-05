const router = require("express").Router();

router.post('/webhook', (req, res) => res.json({ message: "POST /line/webhook" }));
router.get('/logs', (req, res) => res.json({ message: "GET /line/logs" }));
router.get('/messages', (req, res) => res.json({ message: "GET /line/messages" }));
router.get('/actions', (req, res) => res.json({ message: "GET /line/actions" }));
router.post('/test-message', (req, res) => res.json({ message: "POST /line/test-message" }));

module.exports = router;