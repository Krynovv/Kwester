import { Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import QuestsPage from './pages/QuestsPage'
import RewardsPage from './pages/RewardsPage'
import ShopPage from './pages/ShopPage'
import ProfilePage from './pages/ProfilePage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/quests" element={<QuestsPage />} />
          <Route path="/rewards" element={<RewardsPage />} />
          <Route path="/shop" element={<ShopPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default App
