const router = require("express").Router();

router.post('/resend/:id', (req, res) => res.json({ message: `POST /notifications/${req.params.id}` }));
router.get('/', (req, res) => res.json({ message: "GET /notifications" }));

module.exports = router;