import { useState } from 'react'
import './App.css'

function App() {
  const [tasks, setTasks] = useState([])
  const [newTask, setNewTask] = useState('')

  const addTask = () => {
    if (newTask.trim() !== '') {
      setTasks([...tasks, {
        id: Date.now(),
        text: newTask,
        completed: false
      }])
      setNewTask('')
    }
  }

  const toggleTask = (id) => {
    setTasks(tasks.map(task =>
      task.id === id ? { ...task, completed: !task.completed } : task
    ))
  }

  const deleteTask = (id) => {
    setTasks(tasks.filter(task => task.id !== id))
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      addTask()
    }
  }

  return (
    <div className="app">
      <div className="container">
        <h1>QuickTasks</h1>
        <p className="subtitle">Simple task management made easy</p>

        <div className="input-section">
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Add a new task..."
            className="task-input"
          />
          <button onClick={addTask} className="add-button">
            Add Task
          </button>
        </div>

        <div className="tasks-container">
          {tasks.length === 0 ? (
            <p className="empty-state">No tasks yet. Add one above!</p>
          ) : (
            tasks.map(task => (
              <div key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
                <div className="task-content" onClick={() => toggleTask(task.id)}>
                  <span className="task-text">{task.text}</span>
                </div>
                <button onClick={() => deleteTask(task.id)} className="delete-button">
                  Delete
                </button>
              </div>
            ))
          )}
        </div>

        <div className="stats">
          <p>{tasks.filter(task => !task.completed).length} tasks remaining</p>
        </div>
      </div>
    </div>
  )
}

export default App
