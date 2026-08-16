// hooks/useOptimization.js — Polling hook for async optimization task
import { useState, useEffect, useRef } from 'react'
import { optimizeApi } from '../api/client'

const POLL_INTERVAL_MS = 3000  // Poll every 3 seconds
const MAX_POLLS = 100          // 100 × 3s = 5 minutes max

export function useOptimization() {
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState('idle')   // idle|pending|running|completed|failed|timeout
  const [result, setResult] = useState(null)
  const [error, setError]   = useState(null)
  const [progress, setProgress] = useState(0)    // 0-100 estimated
  const pollCount = useRef(0)
  const pollTimer = useRef(null)

  // Start a new optimization run
  const startOptimization = async (params) => {
    setStatus('pending')
    setResult(null)
    setError(null)
    setProgress(5)
    pollCount.current = 0

    try {
      const res = await optimizeApi.start(params)
      setTaskId(res.data.task_id)
      setStatus('pending')
    } catch (err) {
      const msg = err.response?.data?.detail || err.message
      setError(msg)
      setStatus('failed')
    }
  }

  // Poll until terminal state
  useEffect(() => {
    if (!taskId || ['completed', 'failed', 'timeout'].includes(status)) return

    pollTimer.current = setInterval(async () => {
      pollCount.current += 1
      // Fake progress: ease toward 90% while running
      setProgress((p) => Math.min(p + (90 - p) * 0.12, 89))

      if (pollCount.current > MAX_POLLS) {
        clearInterval(pollTimer.current)
        setStatus('timeout')
        setError('Solver melebihi batas waktu 5 menit.')
        return
      }

      try {
        const res = await optimizeApi.getResult(taskId)
        const { status: s, result: r, error_message } = res.data

        setStatus(s)
        if (s === 'completed') {
          setResult(r)
          setProgress(100)
          clearInterval(pollTimer.current)
        } else if (s === 'failed') {
          setError(error_message || 'Optimasi gagal.')
          clearInterval(pollTimer.current)
        }
      } catch (err) {
        // Transient network error — keep polling
        console.warn('Poll error (will retry):', err.message)
      }
    }, POLL_INTERVAL_MS)

    return () => clearInterval(pollTimer.current)
  }, [taskId])

  const reset = () => {
    clearInterval(pollTimer.current)
    setTaskId(null)
    setStatus('idle')
    setResult(null)
    setError(null)
    setProgress(0)
    pollCount.current = 0
  }

  return { status, result, error, progress, taskId, startOptimization, reset }
}
