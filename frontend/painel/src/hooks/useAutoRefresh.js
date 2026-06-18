import { useEffect, useRef } from 'react'

/**
 * Executes a callback on an interval, and optionally whenever
 * dependencies change. Cleans up on unmount.
 *
 * @param {Function} callback - The function to call on each tick.
 * @param {number} intervalMs  - Interval in milliseconds (default 30s).
 * @param {Array}   deps       - When these change, the interval is reset.
 */
export function useAutoRefresh(callback, intervalMs = 30000, deps = []) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    // Fire immediately
    savedCallback.current()

    const id = setInterval(() => {
      savedCallback.current()
    }, intervalMs)

    return () => clearInterval(id)
  }, [intervalMs, ...deps])
}
