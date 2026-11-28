
import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 10
const MIN_EVENT_DATE = '2020-01-01'
const MAX_EVENT_DATE = '2100-12-31'

// Validate the event date
function isValidEventDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false

  if (value < MIN_EVENT_DATE || value > MAX_EVENT_DATE) {
    return false
  }

  const [year, month, day] = value.split('-').map(Number)
  const parsed = new Date(Date.UTC(year, month - 1, day))

  return (
    parsed.getUTCFullYear() === year &&
    parsed.getUTCMonth() + 1 === month &&
    parsed.getUTCDate() === day
  )
}

const EMPTY_FORM = {
  title: '',
  description: '',
  date: '',
  location: '',
}

const EMPTY_FILTERS = {
  title: '',
  location: '',
  date: '',
}

function App() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)

  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [appliedFilters, setAppliedFilters] = useState(EMPTY_FILTERS)
  const [page, setPage] = useState(0)

  // AI assistant state
  const [question, setQuestion] = useState('')

  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hello! I am your CampusConnect AI assistant. Ask me about campus events, dates, locations, and descriptions.',
    },
  ])

  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')

  // Fetch campus events
  const fetchEvents = useCallback(
    async (pageToLoad = page) => {
      const params = new URLSearchParams()

      if (appliedFilters.title.trim()) {
        params.set('title', appliedFilters.title.trim())
      }

      if (appliedFilters.location.trim()) {
        params.set('location', appliedFilters.location.trim())
      }

      if (appliedFilters.date) {
        params.set('date', appliedFilters.date)
      }

      params.set('skip', String(pageToLoad * PAGE_SIZE))
      params.set('limit', String(PAGE_SIZE))

      const response = await fetch(
        `${API_URL}/events?${params.toString()}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch events')
      }

      return response.json()
    },
    [appliedFilters, page]
  )

  // Load events when filters or page changes
  useEffect(() => {
    let ignore = false

    async function loadEvents() {
      try {
        const data = await fetchEvents()

        if (!ignore) {
          setEvents(data)
          setError('')
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message)
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    loadEvents()

    return () => {
      ignore = true
    }
  }, [fetchEvents])

  // Handle event form changes
  function handleChange(event) {
    const { name, value } = event.target

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  // Create or update an event
  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    const isEditing = editingId !== null

    // Reject invalid dates
    if (!isValidEventDate(form.date)) {
      setError(
        'Choose a valid event date between 2020 and 2100.'
      )
      return
    }

    // Confirm date before saving
    const action = isEditing ? 'Update' : 'Create'

    const confirmed = window.confirm(
      `${action} "${form.title}" with date ${form.date}?`
    )

    if (!confirmed) {
      return
    }

    setSubmitting(true)

    try {
      const response = await fetch(
        isEditing
          ? `${API_URL}/events/${editingId}`
          : `${API_URL}/events`,
        {
          method: isEditing ? 'PUT' : 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(form),
        }
      )

      if (!response.ok) {
        const data = await response.json()

        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : data.detail?.[0]?.msg ||
                'Failed to save event'
        )
      }

      await response.json()

      setForm(EMPTY_FORM)
      setEditingId(null)

      const targetPage = isEditing ? page : 0

      if (!isEditing) {
        setPage(0)
      }

      const updatedEvents = await fetchEvents(targetPage)
      setEvents(updatedEvents)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  // Load an event into the edit form
  function handleEdit(event) {
    setEditingId(event.id)

    setForm({
      title: event.title,
      description: event.description,
      date: event.date,
      location: event.location,
    })

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  // Delete an event
  async function handleDelete(eventId) {
    const confirmed = window.confirm(
      'Are you sure you want to delete this event?'
    )

    if (!confirmed) return

    setError('')

    try {
      const response = await fetch(
        `${API_URL}/events/${eventId}`,
        {
          method: 'DELETE',
        }
      )

      if (!response.ok) {
        const data = await response.json()

        throw new Error(
          data.detail || 'Failed to delete event'
        )
      }

      const updatedEvents = await fetchEvents()
      setEvents(updatedEvents)

      if (editingId === eventId) {
        cancelEdit()
      }
    } catch (err) {
      setError(err.message)
    }
  }

  // Cancel editing
  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setError('')
  }

  // Handle filter changes
  function handleFilterChange(event) {
    const { name, value } = event.target

    setFilters((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  // Apply search filters
  function handleFilterSubmit(event) {
    event.preventDefault()
    setPage(0)
    setAppliedFilters({ ...filters })
  }

  // Clear search filters
  function clearFilters() {
    setFilters(EMPTY_FILTERS)
    setAppliedFilters(EMPTY_FILTERS)
    setPage(0)
  }

  // Send a question to the AI backend
  async function handleAskAI(event) {
    event.preventDefault()

    const trimmedQuestion = question.trim()

    if (!trimmedQuestion || chatLoading) return

    setChatError('')
    setQuestion('')
    setChatLoading(true)

    setChatMessages((previous) => [
      ...previous,
      {
        role: 'user',
        content: trimmedQuestion,
      },
    ])

    try {
      const response = await fetch(`${API_URL}/ai/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      })

      if (!response.ok) {
        const data = await response.json()

        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'The AI assistant could not answer your question.'
        )
      }

      const data = await response.json()

      setChatMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.answer,
          eventsUsed: data.events_used,
        },
      ])
    } catch (err) {
      setChatError(err.message)
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>CampusConnect</h1>
        <p>Discover and manage campus events</p>
      </header>

      <section className="events-section">

        {/* AI CAMPUS ASSISTANT */}
        <section className="ai-section">
          <div className="ai-heading">
            <div>
              <h2>CampusConnect AI Assistant</h2>
              <p>
                Ask questions about campus events using AI.
              </p>
            </div>

            <span className="ai-status">
              AI Powered
            </span>
          </div>

          <div
            className="chat-messages"
            aria-live="polite"
          >
            {chatMessages.map((message, index) => (
              <div
                className={`chat-message ${message.role}`}
                key={index}
              >
                <strong>
                  {message.role === 'assistant'
                    ? 'AI Assistant'
                    : 'You'}
                </strong>

                <p>{message.content}</p>

                {message.eventsUsed !== undefined && (
                  <small>
                    Based on {message.eventsUsed} campus
                    event record(s)
                  </small>
                )}
              </div>
            ))}

            {chatLoading && (
              <div className="chat-message assistant">
                <strong>AI Assistant</strong>
                <p>Thinking... Please wait.</p>
              </div>
            )}
          </div>

          {chatError && (
            <p className="error" role="alert">
              {chatError}
            </p>
          )}

          <form
            className="chat-form"
            onSubmit={handleAskAI}
          >
            <input
              type="text"
              placeholder="Ask about campus events..."
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              disabled={chatLoading}
              aria-label="Ask the AI assistant a question"
            />

            <button
              type="submit"
              disabled={chatLoading || !question.trim()}
            >
              {chatLoading ? 'Thinking...' : 'Send'}
            </button>
          </form>

          <p className="chat-hint">
            Example: What campus events are available?
          </p>
        </section>

        {/* CREATE AND UPDATE EVENTS */}
        <h2>
          {editingId !== null
            ? 'Edit Campus Event'
            : 'Create a Campus Event'}
        </h2>

        <form onSubmit={handleSubmit}>
          <input
            name="title"
            placeholder="Event title"
            value={form.title}
            onChange={handleChange}
            required
          />

          <textarea
            name="description"
            placeholder="Event description"
            value={form.description}
            onChange={handleChange}
            required
          />

          <input
            type="date"
            name="date"
            value={form.date}
            onChange={handleChange}
            min={MIN_EVENT_DATE}
            max={MAX_EVENT_DATE}
            aria-label="Event date"
            required
          />

          {form.date && (
            <p>
              Date to save:{' '}
              <strong>{form.date}</strong>.
              Check the year, month and day before
              submitting.
            </p>
          )}

          <input
            name="location"
            placeholder="Event location"
            value={form.location}
            onChange={handleChange}
            required
          />

          <button
            type="submit"
            disabled={submitting}
          >
            {submitting
              ? 'Saving...'
              : editingId !== null
                ? 'Update Event'
                : 'Create Event'}
          </button>

          {editingId !== null && (
            <button
              type="button"
              onClick={cancelEdit}
              disabled={submitting}
            >
              Cancel Edit
            </button>
          )}
        </form>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        {/* SEARCH FILTERS */}
        <h2>Search Campus Events</h2>

        <form
          onSubmit={handleFilterSubmit}
          className="filter-form"
        >
          <input
            name="title"
            placeholder="Search by event title"
            value={filters.title}
            onChange={handleFilterChange}
          />

          <input
            name="location"
            placeholder="Search by location"
            value={filters.location}
            onChange={handleFilterChange}
          />

          <input
            type="date"
            name="date"
            value={filters.date}
            onChange={handleFilterChange}
          />

          <div className="filter-actions">
            <button type="submit">
              Search Events
            </button>

            <button
              type="button"
              onClick={clearFilters}
            >
              Clear Filters
            </button>
          </div>
        </form>

        {/* EVENT LIST */}
        <h2>Campus Events</h2>

        {loading && (
          <p>Loading events...</p>
        )}

        {!loading && events.length === 0 && (
          <p>No matching events found.</p>
        )}

        <div className="events-list">
          {events.map((event) => (
            <article
              className="event-card"
              key={event.id}
            >
              <h3>{event.title}</h3>

              <p>{event.description}</p>

              <p>
                <strong>Date:</strong> {event.date}
              </p>

              <p>
                <strong>Location:</strong>{' '}
                {event.location}
              </p>

              <button
                type="button"
                onClick={() => handleEdit(event)}
              >
                Edit
              </button>

              <button
                type="button"
                onClick={() => handleDelete(event.id)}
              >
                Delete
              </button>
            </article>
          ))}
        </div>

        {/* PAGINATION */}
        <div className="pagination">
          <button
            type="button"
            onClick={() =>
              setPage((previous) => previous - 1)
            }
            disabled={page === 0 || loading}
          >
            Previous
          </button>

          <span>Page {page + 1}</span>

          <button
            type="button"
            onClick={() =>
              setPage((previous) => previous + 1)
            }
            disabled={
              events.length < PAGE_SIZE || loading
            }
          >
            Next
          </button>
        </div>
      </section>
    </main>
  )
}

export default App
