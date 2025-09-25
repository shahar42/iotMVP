import express from 'express';
import { Pool } from 'pg';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'dist')));

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

const jokes = [
  "Why don't scientists trust atoms? Because they make up everything!",
  "Why did the scarecrow win an award? He was outstanding in his field!",
  "Why don't eggs tell jokes? They'd crack each other up!",
  "What do you call a fake noodle? An impasta!",
  "Why did the math book look so sad? Because it had too many problems!",
  "What do you call a bear with no teeth? A gummy bear!",
  "Why can't a bicycle stand up by itself? It's two tired!",
  "What do you call a sleeping bull? A bulldozer!",
  "Why don't some couples go to the gym? Because some relationships don't work out!",
  "What's the best thing about Switzerland? I don't know, but the flag is a big plus!"
];

async function initializeDatabase() {
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS favorite_jokes (
        id SERIAL PRIMARY KEY,
        joke TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('Database initialized');
  } catch (err) {
    console.error('Database initialization error:', err);
  }
}

app.get('/api/random-joke', (req, res) => {
  const randomJoke = jokes[Math.floor(Math.random() * jokes.length)];
  res.json({ joke: randomJoke });
});

app.get('/api/favorites', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM favorite_jokes ORDER BY created_at DESC');
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching favorites:', err);
    res.status(500).json({ error: 'Failed to fetch favorites' });
  }
});

app.post('/api/favorites', async (req, res) => {
  const { joke } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO favorite_jokes (joke) VALUES ($1) RETURNING *',
      [joke]
    );
    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error adding favorite:', err);
    res.status(500).json({ error: 'Failed to add favorite' });
  }
});

app.delete('/api/favorites/:id', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query('DELETE FROM favorite_jokes WHERE id = $1', [id]);
    res.json({ success: true });
  } catch (err) {
    console.error('Error deleting favorite:', err);
    res.status(500).json({ error: 'Failed to delete favorite' });
  }
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

initializeDatabase().then(() => {
  app.listen(port, () => {
    console.log(`Server running on port ${port}`);
  });
});