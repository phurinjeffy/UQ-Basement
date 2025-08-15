
import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="drawer-side">
      <label htmlFor="my-drawer" aria-label="close sidebar" className="drawer-overlay"></label>
      <ul className="menu bg-gray-200 dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-full w-80 p-4">
        <li>
          <Link to="/" className="hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg p-2">Home</Link>
        </li>
        <li>
          <Link to="/dashboard" className="hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg p-2">Dashboard</Link>
        </li>
        <li>
          <Link to="/notfound" className="hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg p-2">NotFound (404)</Link>
        </li>
      </ul>
    </div>
  );
}

export default Sidebar;
