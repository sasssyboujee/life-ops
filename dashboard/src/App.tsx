import { useState, useEffect } from 'react'
import { 
  RefreshCw, 
  DollarSign, 
  Activity, 
  X, 
  ImageIcon, 
  PlusCircle, 
  Dumbbell 
} from 'lucide-react'
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid 
} from 'recharts'

interface Transaction {
  id: number
  timestamp: string
  merchant: string
  category: string
  amount_sgd: number
  notes: string
  has_image: boolean
}

interface Workout {
  id: number
  timestamp: string
  exercise: string
  sets: number
  reps: number
  weight_kg: number
  rpe: number
  fatigue_flags: string
  has_image: boolean
}

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [workouts, setWorkouts] = useState<Workout[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedImage, setSelectedImage] = useState<{ url: string; caption: string } | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [transRes, workRes] = await Promise.all([
        fetch('/api/transactions'),
        fetch('/api/workouts')
      ])
      if (transRes.ok) {
        const data = await transRes.json()
        setTransactions(data)
      }
      if (workRes.ok) {
        const data = await workRes.json()
        setWorkouts(data)
      }
    } catch (error) {
      console.error("Error fetching data:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Process financial chart data
  const categoryDataMap = transactions.reduce((acc, curr) => {
    acc[curr.category] = (acc[curr.category] || 0) + curr.amount_sgd
    return acc
  }, {} as Record<string, number>)

  const categoryChartData = Object.entries(categoryDataMap).map(([name, value]) => ({
    name,
    value
  }))

  const PIE_COLORS = ['#319795', '#4fd1c5', '#2c5282', '#3182ce', '#805ad5', '#b7791f']

  // Process workout chart data
  const workoutChartData = [...workouts]
    .reverse() // Sort chronologically for timeline
    .map(w => ({
      date: new Date(w.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      volume: w.sets * w.reps * w.weight_kg,
      exercise: w.exercise
    }))

  const totalExpenses = transactions.reduce((acc, curr) => acc + curr.amount_sgd, 0)
  
  // Calculate athletic volume peak
  const peakWorkoutVolume = workouts.length 
    ? Math.max(...workouts.map(w => w.sets * w.reps * w.weight_kg))
    : 0

  return (
    <div className="app-container">
      <header>
        <div>
          <h1>⚡ Life Operations Engine</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '4px' }}>
            Decentralized personal tracker ledger • Antigravity Multi-Agent Orchestrator
          </p>
        </div>
        <button className="refresh-button" onClick={fetchData} disabled={loading}>
          <RefreshCw className={loading ? 'animate-spin' : ''} size={18} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </header>

      <main className="dashboard-grid">
        {/* --- Financial Column --- */}
        <section className="dashboard-card financial">
          <div className="card-title">
            <span className="icon-wrapper">
              <DollarSign size={24} />
            </span>
            <h2>Financial Dashboard</h2>
          </div>

          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-label">Total Expenses</div>
              <div className="metric-value">${totalExpenses.toFixed(2)} SGD</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Transactions</div>
              <div className="metric-value">{transactions.length} logged</div>
            </div>
          </div>

          <div className="chart-container">
            {categoryChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a202c', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}
                    itemStyle={{ color: '#E2E8F0' }}
                    formatter={(value) => [`$${Number(value).toFixed(2)} SGD`, 'Spending']}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                No spending data logged yet
              </div>
            )}
          </div>

          <div>
            <h3 className="section-subtitle" style={{ marginBottom: '12px' }}>Recent Ledger Entries</h3>
            <div className="table-wrapper">
              {transactions.length > 0 ? (
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Merchant</th>
                      <th>Category</th>
                      <th>Amount</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.slice(0, 5).map(t => (
                      <tr key={t.id}>
                        <td>{new Date(t.timestamp).toLocaleDateString()}</td>
                        <td>{t.merchant}</td>
                        <td>
                          <span style={{ 
                            background: 'rgba(79, 209, 197, 0.15)', 
                            color: 'var(--accent-teal)', 
                            padding: '4px 8px', 
                            borderRadius: '6px',
                            fontSize: '0.8rem',
                            fontWeight: 600
                          }}>
                            {t.category}
                          </span>
                        </td>
                        <td>${t.amount_sgd.toFixed(2)} SGD</td>
                        <td>
                          {t.notes} {t.has_image && <span title="Image Attached" style={{ color: 'var(--accent-teal)', marginLeft: '4px' }}>🖼️</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No transaction ledger records.
                </div>
              )}
            </div>
          </div>

          {/* Photo Previews */}
          {transactions.some(t => t.has_image) && (
            <div className="photo-previews">
              <h3 className="section-subtitle">🖼️ Logged Receipts</h3>
              <div className="photo-grid">
                {transactions.filter(t => t.has_image).slice(0, 6).map(t => (
                  <div 
                    key={t.id} 
                    className="photo-card"
                    onClick={() => setSelectedImage({
                      url: `/api/transactions/${t.id}/image`,
                      caption: `${t.merchant} • $${t.amount_sgd.toFixed(2)} SGD (${new Date(t.timestamp).toLocaleDateString()})`
                    })}
                  >
                    <img src={`/api/transactions/${t.id}/image`} alt={t.merchant} />
                    <div className="photo-caption">{t.merchant}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* --- Athletic Column --- */}
        <section className="dashboard-card athletic">
          <div className="card-title">
            <span className="icon-wrapper">
              <Activity size={24} />
            </span>
            <h2>Athletic Performance</h2>
          </div>

          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-label">Peak Set Volume</div>
              <div className="metric-value">{peakWorkoutVolume.toLocaleString()} kg*reps</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Workouts</div>
              <div className="metric-value">{workouts.length} logged</div>
            </div>
          </div>

          <div className="chart-container">
            {workoutChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={workoutChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="var(--text-secondary)" tickLine={false} style={{ fontSize: '0.8rem' }} />
                  <YAxis stroke="var(--text-secondary)" tickLine={false} style={{ fontSize: '0.8rem' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a202c', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}
                    labelStyle={{ fontWeight: 600, color: '#f1f5f9' }}
                    itemStyle={{ color: '#E2E8F0' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="volume" 
                    name="Volume (kg*reps)" 
                    stroke="var(--accent-violet)" 
                    strokeWidth={3} 
                    dot={{ fill: 'var(--accent-violet)', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                No training logs recorded yet
              </div>
            )}
          </div>

          <div>
            <h3 className="section-subtitle" style={{ marginBottom: '12px' }}>Exercise Details</h3>
            <div className="table-wrapper">
              {workouts.length > 0 ? (
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Exercise</th>
                      <th>Sets</th>
                      <th>Reps</th>
                      <th>Weight</th>
                      <th>RPE</th>
                      <th>Fatigue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workouts.slice(0, 5).map(w => (
                      <tr key={w.id}>
                        <td>{new Date(w.timestamp).toLocaleDateString()}</td>
                        <td style={{ fontWeight: 600 }}>{w.exercise}</td>
                        <td>{w.sets}</td>
                        <td>{w.reps}</td>
                        <td>{w.weight_kg} kg</td>
                        <td>
                          <span style={{ 
                            background: w.rpe >= 8 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                            color: w.rpe >= 8 ? '#f87171' : 'var(--text-primary)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontWeight: 600
                          }}>
                            {w.rpe}
                          </span>
                        </td>
                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          {w.fatigue_flags || 'None'} {w.has_image && <span title="Workout Photo Attached" style={{ color: 'var(--accent-violet)', marginLeft: '4px' }}>📸</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No athletic tracker records.
                </div>
              )}
            </div>
          </div>

          {/* Photo Previews */}
          {workouts.some(w => w.has_image) && (
            <div className="photo-previews">
              <h3 className="section-subtitle">📸 Workout Log Photos</h3>
              <div className="photo-grid">
                {workouts.filter(w => w.has_image).slice(0, 6).map(w => (
                  <div 
                    key={w.id} 
                    className="photo-card"
                    onClick={() => setSelectedImage({
                      url: `/api/workouts/${w.id}/image`,
                      caption: `${w.exercise} • ${w.sets}x${w.reps} @ ${w.weight_kg}kg (${new Date(w.timestamp).toLocaleDateString()})`
                    })}
                  >
                    <img src={`/api/workouts/${w.id}/image`} alt={w.exercise} />
                    <div className="photo-caption">{w.exercise}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>

      {/* --- Fullscreen Image Modal Overlay --- */}
      {selectedImage && (
        <div className="modal-overlay" onClick={() => setSelectedImage(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setSelectedImage(null)}>
              <X size={20} />
            </button>
            <img src={selectedImage.url} alt="Fullscreen Preview" />
            <div className="modal-caption">{selectedImage.caption}</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
