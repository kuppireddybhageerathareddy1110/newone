import React from 'react'

export default function Toast({ toasts }) {
  return (
    <>
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`toast${toast.show ? ' show' : ''}`}
          dangerouslySetInnerHTML={{ __html: toast.html }}
        />
      ))}
    </>
  )
}
