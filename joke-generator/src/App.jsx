import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [currentJoke, setCurrentJoke] = useState('')
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchRandomJoke = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/random-joke')
      const data = await response.json()
      setCurrentJoke(data.joke)
    } catch (error) {
      console.error('Error fetching joke:', error)
      setCurrentJoke('Sorry, failed to load a joke!')
    } finally {
      setLoading(false)
    }
  }

  const fetchFavorites = async () => {
    try {
      const response = await fetch('/api/favorites')
      const data = await response.json()
      setFavorites(data)
    } catch (error) {
      console.error('Error fetching favorites:', error)
    }
  }

  const addToFavorites = async () => {
    if (!currentJoke) return
    try {
      await fetch('/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ joke: currentJoke })
      })
      fetchFavorites()
    } catch (error) {
      console.error('Error adding favorite:', error)
    }
  }

  const removeFavorite = async (id) => {
    try {
      await fetch(`/api/favorites/${id}`, { method: 'DELETE' })
      fetchFavorites()
    } catch (error) {
      console.error('Error removing favorite:', error)
    }
  }

  useEffect(() => {
    fetchRandomJoke()
    fetchFavorites()
  }, [])

  return (
    <div className="App">
      <header>
        <h1>🃏 Random Joke Generator</h1>
        <p>Get a laugh and save your favorites!</p>
      </header>

      <main>
        <div className="joke-section">
          <div className="joke-card">
            {loading ? (
              <p className="loading">Loading...</p>
            ) : (
              <p className="joke">{currentJoke}</p>
            )}
          </div>

          <div className="joke-actions">
            <button onClick={fetchRandomJoke} disabled={loading} className="primary-btn">
              {loading ? 'Loading...' : 'New Joke'}
            </button>
            <button onClick={addToFavorites} disabled={!currentJoke} className="favorite-btn">
              ⭐ Save Favorite
            </button>
          </div>
        </div>

        <div className="favorites-section">
          <h2>Your Favorite Jokes ({favorites.length})</h2>
          {favorites.length === 0 ? (
            <p className="no-favorites">No favorites yet! Save some jokes you love.</p>
          ) : (
            <div className="favorites-list">
              {favorites.map((favorite) => (
                <div key={favorite.id} className="favorite-item">
                  <p>{favorite.joke}</p>
                  <button onClick={() => removeFavorite(favorite.id)} className="remove-btn">
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App