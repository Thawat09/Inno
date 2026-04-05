const express = require("express");
const app = express();
const routes = require("./src/routes");
const config = require("./src/config/config");

// Middlewares พื้นฐาน
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ใช้งาน Router หลัก
app.use("/", routes);

// Fallback 404
app.use((req, res, next) => {
  res.status(404).json({ error: "Endpoint not found" });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: "Internal Server Error" });
});

app.listen(config.port, () => {
  console.log(`Server running on port ${config.port}`);
  console.log(`API Base URL: /api/v${config.apiVersion}`);
});
