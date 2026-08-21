import { NavLink, Outlet } from 'react-router-dom'

function Layout() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Purchase Approval</p>
          <h1>Solicitudes de compra</h1>
        </div>
        <nav className="nav">
          <NavLink to="/">Solicitudes</NavLink>
          <NavLink to="/requests/new">Nueva solicitud</NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
