function Sidebar() {
  return (
    <div className="drawer-side">
      <label htmlFor="my-drawer" aria-label="close sidebar" className="drawer-overlay"></label>
      <ul className="menu bg-gray-200 dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-full w-80 p-4">
        <li>
          <a className="hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg p-2">Sidebar Item 1</a>
        </li>
        <li>
          <a className="hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg p-2">Sidebar Item 2</a>
        </li>
        <li>
          <a className="hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg p-2">Sidebar Item 3</a>
        </li>
      </ul>
    </div>
  );
}

export default Sidebar;
