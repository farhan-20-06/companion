const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

// In-memory storage for demonstration
const speedData = [];

// POST endpoint to insert speed limit and speed
app.post('/api/speed', (req, res) => {
  const { vehicleId, speed, speedLimit } = req.body;
  if (
    typeof vehicleId !== 'string' ||
    typeof speed !== 'number' ||
    typeof speedLimit !== 'number'
  ) {
    return res.status(400).json({ error: 'Invalid input. vehicleId (string), speed (number), speedLimit (number) required.' });
  }
  speedData.push({ vehicleId, speed, speedLimit, timestamp: Date.now() });
  res.status(201).json({ message: 'Speed data inserted successfully.' });
});

// Optional: GET endpoint to view all speed data
app.get('/api/speed', (req, res) => {
  res.json(speedData);
});

app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
}); 