const db = require('./db');

db.query('SELECT * FROM traffic_db', (err, results) => {
  if (err) {
    console.error('Query error:', err);
    return;
  }
  console.log('Query results:', results);
});