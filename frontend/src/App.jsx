import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import Layout from './components/Layout'
import CreateRequestPage from './pages/CreateRequestPage'
import RequestDetailPage from './pages/RequestDetailPage'
import RequestsPage from './pages/RequestsPage'
import './App.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <RequestsPage /> },
      { path: 'requests/new', element: <CreateRequestPage /> },
      { path: 'requests/:requestId', element: <RequestDetailPage /> },
    ],
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
