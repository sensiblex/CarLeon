import { Link, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ChainPage } from './pages/ChainPage'
import { DealPage } from './pages/DealPage'
import { DealsPage } from './pages/DealsPage'
import { TrackPage } from './pages/TrackPage'

function NotFound() {
  return (
    <div className="py-20 text-center">
      <p className="text-5xl font-bold text-slate-300">404</p>
      <p className="mt-3 text-slate-600">Такой страницы нет.</p>
      <Link to="/" className="mt-4 inline-block text-sm font-medium text-brand-600 hover:underline">
        На главную
      </Link>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<TrackPage />} />
        <Route path="deals" element={<DealsPage />} />
        <Route path="deals/:trackCode" element={<DealPage />} />
        <Route path="blockchain" element={<ChainPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
