const router = require("express").Router();

router.post('/chat/session', (req, res) => res.json({ message: "POST /ai/chat/session" }));
router.post('/chat/message', (req, res) => res.json({ message: "POST /ai/chat/message" }));
router.get('/chat/sessions', (req, res) => res.json({ message: "GET /ai/chat/sessions" }));
router.get('/chat/sessions/:id/messages', (req, res) => res.json({ message: `GET /ai/chat/sessions/${req.params.id}/messages` }));
router.post('/chat/feedback', (req, res) => res.json({ message: "POST /ai/chat/feedback" }));

module.exports = router;