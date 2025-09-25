const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

const quotes = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Innovation distinguishes between a leader and a follower. - Steve Jobs",
    "Your time is limited, so don’t waste it living someone else’s life. - Steve Jobs"
];

app.get('/api/quote', (req, res) => {
    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    res.json({ quote: randomQuote });
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});