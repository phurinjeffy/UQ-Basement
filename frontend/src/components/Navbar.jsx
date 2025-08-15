function Navbar() {
  return (
    <div className="navbar bg-base-100 shadow-sm z-50">
      <div className="navbar-start">
        {/* Old hamburger toggle button */}
        <label htmlFor="my-drawer" className="btn btn-ghost btn-circle drawer-button">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7" />
          </svg>
        </label>
      </div>
      <div className="navbar-center">
        <a className="btn btn-ghost text-xl">UQ basement</a>
      </div>
      <div className="navbar-end">
        <div className="dropdown dropdown-end">
          <div tabIndex={0} role="button" className="btn btn-ghost btn-circle avatar">
            <div className="avatar avatar-placeholder">
              <div className="bg-neutral text-neutral-content w-9 rounded-full">
                <span>SY</span>
              </div>
            </div>
          </div>
          <ul
            tabIndex={0}
            className="menu menu-sm dropdown-content bg-base-100 rounded-box z-1 mt-3 w-36 p-2 shadow">
            <li><a className="justify-between">Profile</a></li>
            <li><a>Settings</a></li>
            <li><a>Logout</a></li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Navbar;
