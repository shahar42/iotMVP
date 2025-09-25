import { useState, useEffect } from 'react'

function App() {
  const [quote, setQuote] = useState('')

  useEffect(() => {
    fetch('/api/quote')
      .then(res => res.json())
      .then(data => setQuote(data.quote))
  }, [])

  return (
    <>
      <h1>Quote of the day</h1>
      <p>{quote}</p>
    </>
  )
}

export default App
