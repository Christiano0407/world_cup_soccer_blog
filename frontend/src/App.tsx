import { BrowserRouter, Routes, Route } from 'react-router-dom'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><h1 className="text-3xl font-bold">World Cup Blog</h1></Layout>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
