const router = require("express").Router();
// const authController = require("../../controllers/auth.controller");
// const authMiddleware = require("../../middlewares/auth.middleware");

// Mock Controller Functions (ในของจริงจะย้ายไปไว้ในโฟลเดอร์ controllers)
router.post('/login', (req, res) => { res.json({ message: "Login endpoint" }) });
router.post('/logout', (req, res) => { res.json({ message: "Logout endpoint" }) });
router.post('/set-password', (req, res) => { res.json({ message: "Set Password endpoint" }) });
router.post('/verify-otp', (req, res) => { res.json({ message: "Verify OTP endpoint" }) });
router.post('/request-reset', (req, res) => { res.json({ message: "Request Reset endpoint" }) });
router.post('/reset-password', (req, res) => { res.json({ message: "Reset Password endpoint" }) });
router.post('/change-password', (req, res) => { res.json({ message: "Change Password endpoint" }) });
router.get('/me', (req, res) => { res.json({ message: "Get Me endpoint" }) });

module.exports = router;