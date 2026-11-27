
import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 10

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

  // Fetch events with search, filters and pagination
  async function fetchEvents() {
    setLoading(true)

    try {
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

      params.set('skip', String(page * PAGE_SIZE))
      params.set('limit', String(PAGE_SIZE))

      const response = await fetch(
        `${API_URL}/events?${params.toString()}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch events')
      }

      const data = await response.json()
      setEvents(data)
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents()
  }, [appliedFilters, page])

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
    setSubmitting(true)

    const isEditing = editingId !== null

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
            : data.detail?.[0]?.msg || 'Failed to save event'
        )
      }

      await response.json()

      setForm(EMPTY_FORM)
      setEditingId(null)

      // Return to first page to show newly created events
      if (!isEditing) {
        setPage(0)
      } else {
        await fetchEvents()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  // Load event details into the form
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
        throw new Error(data.detail || 'Failed to delete event')
      }

      // Reload the current page after deletion
      await fetchEvents()

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

  // Handle filter input changes
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

  return (
    <main className="app">
      <header className="app-header">
        <h1>CampusConnect</h1>
        <p>Discover and manage campus events</p>
      </header>

      <section className="events-section">
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
            required
          />

          <input
            name="location"
            placeholder="Event location"
            value={form.location}
            onChange={handleChange}
            required
          />

          <button type="submit" disabled={submitting}>
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

        {error && <p className="error">{error}</p>}

        <h2>Search Campus Events</h2>

        <form onSubmit={handleFilterSubmit} className="filter-form">
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
            <button type="submit">Search Events</button>

            <button
              type="button"
              onClick={clearFilters}
            >
              Clear Filters
            </button>
          </div>
        </form>

        <h2>Campus Events</h2>

        {loading && <p>Loading events...</p>}

        {!loading && events.length === 0 && (
          <p>No matching events found.</p>
        )}

        <div className="events-list">
          {events.map((event) => (
            <article className="event-card" key={event.id}>
              <h3>{event.title}</h3>

              <p>{event.description}</p>

              <p>
                <strong>Date:</strong> {event.date}
              </p>

              <p>
                <strong>Location:</strong> {event.location}
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

        <div className="pagination">
          <button
            type="button"
            onClick={() => setPage((previous) => previous - 1)}
            disabled={page === 0 || loading}
          >
            Previous
          </button>

          <span>Page {page + 1}</span>

          <button
            type="button"
            onClick={() => setPage((previous) => previous + 1)}
            disabled={events.length < PAGE_SIZE || loading}
          >
            Next
          </button>
        </div>
      </section>
    </main>
  )
}

export default App
