import '../styles/components/toast.css'

export default function Toast({ message, visible }) {
  return <div className={`toast${visible ? ' visible' : ''}`}>{message}</div>
}
